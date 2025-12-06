from __future__ import annotations

import collections

from yt_dlp.extractor.youtube.jsc.provider import (
    JsChallengeProvider,
    JsChallengeProviderError,
    JsChallengeProviderResponse,
    JsChallengeRequest,
    JsChallengeResponse,
    JsChallengeType,
    NChallengeOutput,
    SigChallengeOutput,
    register_preference,
    register_provider,
)
from yt_dlp.extractor.youtube.pot._provider import BuiltinIEContentProvider

try:
    from ytdlp_jsc import solve as _solve
    _HAS_YTDLP_JSC = True
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[2]))
    try:
        from ytdlp_jsc import solve as _solve
        _HAS_YTDLP_JSC = True
    except ImportError:
        _HAS_YTDLP_JSC = False
        _solve = None

@register_provider
class YtdlpJscJCP(JsChallengeProvider, BuiltinIEContentProvider):
    """
    JS Challenge Provider using ytdlp-jsc native module.
    No external JS runtime required.
    """

    PROVIDER_NAME = 'ytdlp-jsc'
    PROVIDER_VERSION = '0.1.5'
    BUG_REPORT_LOCATION = 'https://github.com/ahaoboy/ytdlp-jsc/issues'

    _SUPPORTED_TYPES = [JsChallengeType.N, JsChallengeType.SIG]

    def is_available(self) -> bool:
        return _HAS_YTDLP_JSC

    def _real_bulk_solve(self, requests: list[JsChallengeRequest]):
        if not requests:
            return

        # Group requests by player_url (same as EJSBaseJCP)
        grouped: dict[str, list[JsChallengeRequest]] = collections.defaultdict(list)
        for request in requests:
            grouped[request.input.player_url].append(request)

        for player_url, grouped_requests in grouped.items():
            video_id = next((r.video_id for r in grouped_requests), None)
            try:
                player = self._get_player(video_id, player_url)
            except JsChallengeProviderError as e:
                for request in grouped_requests:
                    yield JsChallengeProviderResponse(request=request, error=e)
                continue

            self.logger.info(f'Solving JS challenges using {self.PROVIDER_NAME}')

            # Build flat challenge list: ["n:xxx", "n:yyy", "sig:zzz", ...]
            challenges = [
                f'{req.type.value}:{challenge}'
                for req in grouped_requests
                for challenge in req.input.challenges
            ]
            try:
                results = _solve(player, challenges)
            except Exception as e:
                error = JsChallengeProviderError(f'ytdlp-jsc failed: {e}')
                for request in grouped_requests:
                    yield JsChallengeProviderResponse(request=request, error=error)
                continue

            # Map results back to requests
            idx = 0
            for request in grouped_requests:
                data = {}
                for challenge in request.input.challenges:
                    data[challenge] = results[idx]
                    idx += 1

                output_cls = NChallengeOutput if request.type is JsChallengeType.N else SigChallengeOutput
                yield JsChallengeProviderResponse(
                    request=request,
                    response=JsChallengeResponse(
                        type=request.type,
                        output=output_cls(data),
                    ),
                )


@register_preference(YtdlpJscJCP)
def preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 1111

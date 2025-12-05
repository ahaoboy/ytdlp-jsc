from __future__ import annotations

import json

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
    _HAS_YTDLP_JSC = False
    _solve = None

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
    PROVIDER_NAME = 'ytdlp-jsc'
    PROVIDER_VERSION = '0.1.5'
    BUG_REPORT_LOCATION = 'https://github.com/ahaoboy/ytdlp-jsc/issues'

    _SUPPORTED_TYPES = [JsChallengeType.N, JsChallengeType.SIG]

    def is_available(self) -> bool:
        return _HAS_YTDLP_JSC

    def _real_bulk_solve(self, requests: list[JsChallengeRequest]):
        if not requests:
            return

        # Group requests by player_url
        grouped: dict[str, list[JsChallengeRequest]] = {}
        for request in requests:
            grouped.setdefault(request.input.player_url, []).append(request)

        for player_url, group_requests in grouped.items():
            video_id = next((r.video_id for r in group_requests if r.video_id), None)
            try:
                player_js = self._get_player(video_id, player_url)
            except JsChallengeProviderError as e:
                for request in group_requests:
                    yield JsChallengeProviderResponse(request=request, error=e)
                continue

            self.logger.info('Solving JS challenges using ytdlp-jsc')

            # Build challenges: ["n:xxx", "sig:yyy", ...]
            challenges = []
            challenge_map = []  # [(request_idx, challenge), ...]
            for idx, req in enumerate(group_requests):
                for challenge in req.input.challenges:
                    challenges.append(f'{req.type.value}:{challenge}')
                    challenge_map.append((idx, challenge))

            # Solve all at once
            try:
                results = json.loads(_solve(player_js, challenges))
            except Exception as e:
                error = JsChallengeProviderError(f'ytdlp-jsc failed: {e}')
                for request in group_requests:
                    yield JsChallengeProviderResponse(request=request, error=error)
                continue

            # Map results back to requests
            results_by_idx: dict[int, dict[str, str]] = {}
            for (idx, challenge), result in zip(challenge_map, results):
                results_by_idx.setdefault(idx, {})[challenge] = result

            # Yield responses
            for idx, request in enumerate(group_requests):
                output_cls = NChallengeOutput if request.type == JsChallengeType.N else SigChallengeOutput
                yield JsChallengeProviderResponse(
                    request=request,
                    response=JsChallengeResponse(
                        type=request.type,
                        output=output_cls(results=results_by_idx.get(idx, {})),
                    ),
                )


@register_preference(YtdlpJscJCP)
def preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 1111

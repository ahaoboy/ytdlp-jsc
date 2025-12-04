from __future__ import annotations

from yt_dlp.extractor.youtube.jsc.provider import (
    JsChallengeProvider,
    JsChallengeProviderError,
    JsChallengeProviderRejectedRequest,
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

from ytdlp_jsc import solve as _solve

@register_provider
class YtdlpJscJCP(JsChallengeProvider, BuiltinIEContentProvider):
    PROVIDER_NAME = 'ytdlp-jsc'
    PROVIDER_VERSION = '0.1.0'
    BUG_REPORT_LOCATION = 'https://github.com/yt-dlp/yt-dlp/issues'

    _SUPPORTED_TYPES = [JsChallengeType.N, JsChallengeType.SIG]

    def is_available(self) -> bool:
        return True

    def _real_bulk_solve(self, requests: list[JsChallengeRequest]):
        if not requests:
            return

        # Group requests by player_url
        grouped: dict[str, list[JsChallengeRequest]] = {}
        for request in requests:
            player_url = request.input.player_url
            if player_url not in grouped:
                grouped[player_url] = []
            grouped[player_url].append(request)

        for player_url, group_requests in grouped.items():
            # Download player.js
            video_id = next((r.video_id for r in group_requests if r.video_id), None)
            try:
                player_js = self._get_player(video_id, player_url)
            except JsChallengeProviderError as e:
                for request in group_requests:
                    yield JsChallengeProviderResponse(request=request, error=e)
                continue

            # Validate player_js
            if not player_js:
                error = JsChallengeProviderError('player_js is empty or None')
                for request in group_requests:
                    yield JsChallengeProviderResponse(request=request, error=error)
                continue

            self.logger.info('Solving JS challenges using ytdlp-jsc')
            self.logger.debug(f'player_js length: {len(player_js)}')

            # Process each request
            for request in group_requests:
                try:
                    result = self._solve_request(player_js, request)
                    yield JsChallengeProviderResponse(request=request, response=result)
                except (JsChallengeProviderError, JsChallengeProviderRejectedRequest) as e:
                    yield JsChallengeProviderResponse(request=request, error=e)

    def _solve_request(self, player_js: str, request: JsChallengeRequest) -> JsChallengeResponse:
        """Solve a single challenge request"""
        challenge_type = request.type.value  # 'n' or 'sig'
        challenges = request.input.challenges
        results = {}

        # Validate challenges
        if not challenges:
            raise JsChallengeProviderRejectedRequest('No challenges provided', expected=True)

        for challenge in challenges:
            # Validate individual challenge
            if not challenge or not isinstance(challenge, str):
                raise JsChallengeProviderError(
                    f'Invalid challenge: {challenge!r} (type: {type(challenge).__name__})')

            self.logger.debug(
                f'Solving {challenge_type}:{challenge[:20]}{"..." if len(challenge) > 20 else ""}')

            try:
                result = _solve(player_js, challenge_type, challenge)

                # Validate result
                if result is None:
                    raise JsChallengeProviderError(
                        f'ytdlp-jsc returned None for {challenge_type}:{challenge}')
                if not isinstance(result, str):
                    raise JsChallengeProviderError(
                        f'ytdlp-jsc returned non-string result: {type(result).__name__}')
                if not result:
                    raise JsChallengeProviderError(
                        f'ytdlp-jsc returned empty string for {challenge_type}:{challenge}')

                results[challenge] = result

            except IndexError as e:
                # Specific handling for "string index out of range"
                raise JsChallengeProviderError(
                    f'Index error in ytdlp-jsc: {e}. '
                    f'This may indicate incompatible player.js format. '
                    f'challenge_type={challenge_type!r}, '
                    f'challenge_len={len(challenge)}, '
                    f'player_js_len={len(player_js)}',
                    expected=False,
                ) from e
            except TypeError as e:
                # Handle type errors (e.g., None passed to string operations)
                raise JsChallengeProviderError(
                    f'Type error in ytdlp-jsc: {e}. '
                    f'challenge_type={challenge_type!r}, '
                    f'challenge={challenge!r}',
                    expected=False,
                ) from e
            except JsChallengeProviderError:
                raise
            except Exception as e:
                raise JsChallengeProviderError(
                    f'ytdlp-jsc solve failed: {type(e).__name__}: {e}',
                    expected=False,
                ) from e

        if request.type == JsChallengeType.N:
            return JsChallengeResponse(type=request.type, output=NChallengeOutput(results=results))
        else:
            return JsChallengeResponse(type=request.type, output=SigChallengeOutput(results=results))


@register_preference(YtdlpJscJCP)
def preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 1111

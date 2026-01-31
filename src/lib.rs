use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod ytdlp_jsc {
    use ytdlp_ejs::{JsChallengeOutput, JsChallengeResponse, RuntimeType, run};
    use pyo3::{exceptions::PyTypeError, prelude::*};

    #[pyfunction]
    fn solve_json(player: String, challenge: Vec<String>) -> PyResult<String> {
        let output = run(player, RuntimeType::QuickJS, challenge)
            .map_err(|e| PyTypeError::new_err(e.to_string()))?;
        serde_json::to_string(&output).map_err(|e| PyTypeError::new_err(e.to_string()))
    }

    #[pyfunction]
    fn solve(player: String, challenges: Vec<String>) -> PyResult<Vec<String>> {
        let output = run(player, RuntimeType::QuickJS, challenges.clone())
            .map_err(|e| PyTypeError::new_err(e.to_string()))?;

        match output {
            JsChallengeOutput::Result { responses, .. } => {
                let mut results = Vec::with_capacity(challenges.len());

                for (challenge, response) in challenges.iter().zip(responses.iter()) {
                    match response {
                        JsChallengeResponse::Result { data } => {
                            // Extract the original challenge value (without type prefix)
                            let challenge_key = challenge
                                .split_once(':')
                                .map(|(_, c)| c)
                                .unwrap_or(challenge);

                            results.push(data.get(challenge_key).cloned().unwrap_or_default());
                        }
                        JsChallengeResponse::Error { error } => {
                            return Err(PyTypeError::new_err(error.clone()));
                        }
                    }
                }

                Ok(results)
            }
            JsChallengeOutput::Error { error } => Err(PyTypeError::new_err(error)),
        }
    }
}

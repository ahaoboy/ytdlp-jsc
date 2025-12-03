use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod ytdlp_jsc {
    use ejs::*;
    use pyo3::{
        exceptions::PyTypeError,
        prelude::*,
    };
    /// Formats the sum of two numbers as string.
    #[pyfunction]
    fn solve(player: String, challenge_type: String, challenge: String) -> PyResult<String> {
        let req_type = match challenge_type.as_str() {
            "n" => RequestType::N,
            "sig" => RequestType::Sig,
            _ => {
                return Err(PyTypeError::new_err(
                    "ERROR: Unsupported request type".to_string(),
                ));
            }
        };
        let input = Input::Player {
            player,
            requests: vec![Request {
                req_type,
                challenges: vec![challenge],
            }],
            output_preprocessed: false,
        };

        let output = process_input_with_runtime(input, RuntimeType::QuickJS);
        serde_json::to_string(&output).map_err(|e| PyTypeError::new_err(e.to_string()))
    }
}

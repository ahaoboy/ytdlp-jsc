use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod ytdlp_jsc {
    use ejs::{RuntimeType, run};
    use pyo3::{exceptions::PyTypeError, prelude::*};
    /// Formats the sum of two numbers as string.
    #[pyfunction]
    fn solve(player: String, challenge: Vec<String>) -> PyResult<String> {
        let output = run(player, RuntimeType::QuickJS, challenge).map_err(|e| PyTypeError::new_err(e.to_string()))?;
        serde_json::to_string(&output).map_err(|e| PyTypeError::new_err(e.to_string()))
    }
}

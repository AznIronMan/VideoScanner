import inspect
import traceback
from types import FrameType


def zerr(e: Exception) -> str:
    return_stmt = str(e)
    current_frame = inspect.currentframe()
    if isinstance(current_frame, FrameType):
        error_frame = current_frame.f_back
        if isinstance(error_frame, FrameType):
            error_line = error_frame.f_lineno
            function_name = error_frame.f_code.co_name
            arg_info = inspect.getargvalues(error_frame)
            function_args_str = ", ".join(
                f"{arg}={error_frame.f_locals[arg]}" for arg in arg_info.args
            )

            tb = traceback.extract_tb(e.__traceback__)

            filename, line_no, function_name, line = tb[-1]
            return_stmt = (
                f"[{filename}:{line_no}]|"
                f"[{function_name}({function_args_str}):{error_line}]|"
                f"[{line}]|[error:{e}]"
            )
    return return_stmt

from pydantic import BaseModel
from  typing import Any

class ApiResponse(BaseModel):
    status: str = "success"
    code: int = 200
    data: Any = None
    message: str = "Request processed successfully"

# Response Wrapper
def api_response(data: Any, message: str = "Request processed successfully"):
    return ApiResponse(status="success", data=data, message=message)
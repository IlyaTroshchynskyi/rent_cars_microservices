from pydantic import BaseModel


class UserMockResponse(BaseModel):
    method: str = 'GET'
    url: str = 'http://test-car-service-host/auth/is-user-logged-in'
    status_code: int = 200

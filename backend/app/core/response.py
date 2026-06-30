from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success(data=None, message: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": jsonable_encoder(data)},
    )


def error(message: str, code: str = "error", status_code: int = 400, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message, "details": jsonable_encoder(details)},
        },
    )

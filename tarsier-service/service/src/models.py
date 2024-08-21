from pydantic import BaseModel
from typing import Literal, Optional


class JsonSchemaValue(BaseModel):
    type: Literal['string', 'number', 'boolean', 'array', 'object']
    description: str
    items: 'JsonSchemaValue' = None
    properties: dict[str, 'JsonSchemaValue'] = None
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'description': self.description,
            'items': self.items.to_dict() if self.items else None,
            'properties': {k: v.to_dict() for k, v in (self.properties or {}).items()}
        }
    
class PageTextData(BaseModel):
    url: str
    options: dict[str, bool] | None = None


class ExtractOptions(BaseModel):
    return_page_text: bool = False

class ExtractData(BaseModel):
    url: str
    outputSchema: dict[str, JsonSchemaValue]
    options: ExtractOptions = None

class ExtractResponseData(BaseModel):
    data: str
    page_text: Optional[str] = None


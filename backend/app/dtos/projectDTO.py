
from pydantic import BaseModel


class ProjectBase(BaseModel):
    project_name: str
    description: str

class CreateProjectRequest(ProjectBase):
    pass




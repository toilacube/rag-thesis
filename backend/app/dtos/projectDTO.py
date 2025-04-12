from pydantic import BaseModel


class ProjectBase(BaseModel):
    project_name: str
    description: str

class CreateProjectRequest(ProjectBase):
    pass

class UpdateProjectRequest(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int

    class Config:
        orm_mode = True




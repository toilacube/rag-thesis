import NewProjectForm from "./new-project-form";

const NewProject = () => {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create Project</h2>
        <p className="text-muted-foreground">
          Create a new project to store your documents
        </p>
      </div>

      <NewProjectForm />
    </div>
  );
};

export default NewProject;

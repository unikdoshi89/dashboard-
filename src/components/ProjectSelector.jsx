function ProjectSelector({
  projects,
  selectedProjectId,
  onChange,
}) {
  return (
    <select
      value={selectedProjectId || ""}
      onChange={(event) =>
        onChange(
          Number(event.target.value)
        )
      }
      className="
        w-64
        border
        border-gray-300
        rounded-lg
        px-4
        py-2.5
        bg-white
        text-sm
        text-gray-700
        outline-none
        focus:ring-2
        focus:ring-blue-500
      "
    >

      <option value="" disabled>
        Select Project
      </option>

      {projects.map((project) => (
        <option
          key={project.id}
          value={project.id}
        >
          {project.name}
        </option>
      ))}

    </select>
  );
}

export default ProjectSelector;

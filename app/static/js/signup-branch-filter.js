(() => {
  const departmentSelect = document.querySelector("[data-department-select]");
  const branchSelect = document.querySelector("[data-branch-select]");
  if (!departmentSelect || !branchSelect) {
    return;
  }

  const branchOptions = Array.from(branchSelect.options).map((option) => ({
    option,
    departmentId: option.dataset.departmentId || "",
  }));

  const syncBranches = () => {
    const selectedDepartment = departmentSelect.value;
    branchSelect.value = "";
    branchOptions.forEach(({ option, departmentId }) => {
      option.hidden = Boolean(departmentId) && departmentId !== selectedDepartment;
      option.disabled = Boolean(departmentId) && departmentId !== selectedDepartment;
    });
  };

  departmentSelect.addEventListener("change", syncBranches);
  syncBranches();
})();

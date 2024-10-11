// Basic scheduling assistant logic
function scheduleTask() {
    const taskInput = document.getElementById('taskInput').value;
    const timeInput = document.getElementById('timeInput').value;
    
    if (taskInput === "" || timeInput === "") {
        alert("Please enter both task and time.");
        return;
    }

    const taskList = document.getElementById('taskList');
    const newTask = document.createElement('li');
    newTask.textContent = `Task: ${taskInput}, Time: ${timeInput}`;
    taskList.appendChild(newTask);

    // Clear the input fields after submission
    document.getElementById('taskInput').value = "";
    document.getElementById('timeInput').value = "";
}

from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Store tasks in a global list (used instead of a CSV)
tasks = []

# Helper function to calculate priority score
def calculate_priority_score(task):
    return task['Urgency'] + task['Importance'] - task['Difficulty'] - (task['Progress'] / 10)

# Route to display the form and handle form submissions
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get data from the form and add it to the tasks list
        task = {
            'Task': request.form['task_name'],
            'Urgency': int(request.form['urgency']),
            'Importance': int(request.form['importance']),
            'Difficulty': int(request.form['difficulty']),
            'Estimated Duration': int(request.form['estimated_duration']),  # Duration in minutes
            'Days on To-Do List': int(request.form['days_on_list']),
            'Progress': int(request.form['progress']),
            'Notes': request.form['notes'],
            'Recurring': 'recurring' in request.form,
            'Completed': False  # Track completion status
        }
        # Calculate priority score
        task['Priority Score'] = calculate_priority_score(task)
        tasks.append(task)
        return redirect(url_for('index'))

    return render_template('index.html')

# Route to display the generated schedule
@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    global tasks

    # Check if it's a POST request to mark tasks as complete or remove them
    if request.method == 'POST':
        task_name = request.form.get('task_name')
        action = request.form.get('action')

        if action == 'complete':
            for task in tasks:
                if task['Task'] == task_name:
                    task['Completed'] = True
        elif action == 'remove':
            tasks = [task for task in tasks if task['Task'] != task_name]
        
        return redirect(url_for('schedule'))

    # Create a DataFrame from the tasks list
    tasks_df = pd.DataFrame(tasks)

    # Sort tasks by priority score if there are any tasks
    if not tasks_df.empty:
        tasks_df = tasks_df.sort_values(by='Priority Score', ascending=False)

    # Define work start and end times (default values)
    work_start_time = pd.Timestamp(datetime.now().strftime('%Y-%m-%d 09:00'))  # Start at 9:00 AM today
    work_end_time = pd.Timestamp(datetime.now().strftime('%Y-%m-%d 17:00'))  # End at 5:00 PM today

    # Create a daily schedule with breaks
    schedule_df = create_schedule(tasks_df, work_start_time, work_end_time)

    # Convert the schedule to a list of dictionaries for display
    schedule_list = schedule_df.to_dict(orient='records')

    return render_template('schedule.html', schedule=schedule_list, tasks=tasks)

# Route to clear all completed tasks
@app.route('/clear_completed', methods=['POST'])
def clear_completed():
    global tasks
    tasks = [task for task in tasks if not task['Completed']]
    return redirect(url_for('schedule'))

# Function to create the daily schedule with breaks
def create_schedule(tasks_df, work_start_time, work_end_time):
    schedule = []
    current_time = work_start_time
    short_break_duration = pd.Timedelta(minutes=15)
    lunch_break_duration = pd.Timedelta(minutes=60)

    # Flag to check if a lunch break has been added
    lunch_break_added = False

    for _, task in tasks_df.iterrows():
        task_duration_minutes = task['Estimated Duration']
        
        # Add the task to the schedule if it fits within the work day
        if current_time + pd.Timedelta(minutes=task_duration_minutes) <= work_end_time:
            end_time = current_time + pd.Timedelta(minutes=task_duration_minutes)
            schedule.append({
                'Task': task['Task'],
                'Start Time': current_time.strftime('%H:%M'),
                'End Time': end_time.strftime('%H:%M'),
                'Priority Score': task['Priority Score'],
                'Notes': task['Notes'],
                'Recurring': task['Recurring'],
                'Completed': task['Completed'],
                'Progress': task['Progress'],
                'Estimated Duration': task_duration_minutes
            })
            current_time = end_time

            # Insert a short break after each task if it fits within the work day
            if current_time + short_break_duration <= work_end_time:
                break_start_time = current_time
                break_end_time = current_time + short_break_duration
                schedule.append({
                    'Task': 'Short Break',
                    'Start Time': break_start_time.strftime('%H:%M'),
                    'End Time': break_end_time.strftime('%H:%M'),
                    'Priority Score': 'N/A',
                    'Notes': '',
                    'Recurring': False,
                    'Completed': False,
                    'Progress': 0,
                    'Estimated Duration': 15
                })
                current_time = break_end_time

            # Insert a lunch break around 12:30 PM if it hasn’t been added yet
            if not lunch_break_added and current_time >= pd.Timestamp(datetime.now().strftime('%Y-%m-%d 12:30')):
                lunch_start_time = current_time
                lunch_end_time = current_time + lunch_break_duration
                schedule.append({
                    'Task': 'Lunch Break',
                    'Start Time': lunch_start_time.strftime('%H:%M'),
                    'End Time': lunch_end_time.strftime('%H:%M'),
                    'Priority Score': 'N/A',
                    'Notes': '',
                    'Recurring': False,
                    'Completed': False,
                    'Progress': 0,
                    'Estimated Duration': 60
                })
                current_time = lunch_end_time
                lunch_break_added = True

    return pd.DataFrame(schedule)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

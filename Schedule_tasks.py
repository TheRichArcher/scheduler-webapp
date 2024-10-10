import pandas as pd

# Function to read the CSV file containing tasks and their progress
def read_tasks(file_path):
    try:
        tasks_df = pd.read_csv(file_path)
        print("CSV file loaded successfully.")
        return tasks_df
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None

# Calculate a priority score for each task based on urgency, importance, difficulty, and progress
def calculate_priority_score(tasks_df):
    # Priority calculation considers urgency, importance, difficulty, and progress
    tasks_df['Priority Score'] = tasks_df['Urgency'] + tasks_df['Importance'] - tasks_df['Difficulty'] - (tasks_df['Progress'] / 10)
    tasks_df = tasks_df.sort_values(by='Priority Score', ascending=False)
    return tasks_df

# Helper function to ensure correct AM/PM formatting
def format_time(time_str, is_start_time=True):
    # Automatically add AM or PM if not provided
    if "AM" not in time_str and "PM" not in time_str:
        if is_start_time:
            return f"{time_str} AM"
        else:
            return f"{time_str} PM"
    return time_str

# Convert 12-hour time format to a pandas Timestamp
def convert_to_timestamp(date_str, time_str, is_start_time=True):
    formatted_time_str = format_time(time_str, is_start_time)
    return pd.Timestamp(f'{date_str} {formatted_time_str}')

# Dynamically insert a lunch break within a flexible time window
def insert_lunch_break(schedule, work_start_time, work_end_time):
    lunch_window_start = pd.Timestamp(f"{work_start_time.date()} 12:30:00")
    lunch_window_end = pd.Timestamp(f"{work_start_time.date()} 14:00:00")
    lunch_duration = pd.Timedelta(minutes=60)  # 1-hour lunch break

    if lunch_window_start < work_end_time:
        for i in range(len(schedule) - 1):
            current_task_end = schedule.loc[i, 'End Time']
            next_task_start = schedule.loc[i + 1, 'Start Time']

            if (lunch_window_start <= current_task_end < lunch_window_end and 
                next_task_start >= current_task_end + lunch_duration):
                lunch_start_time = max(lunch_window_start, current_task_end)
                lunch_end_time = lunch_start_time + lunch_duration

                schedule = pd.concat([
                    schedule.iloc[:i + 1],  # Tasks before lunch
                    pd.DataFrame([{'Task': 'Lunch Break', 'Start Time': lunch_start_time, 'End Time': lunch_end_time, 'Priority Score': 'N/A'}]),
                    schedule.iloc[i + 1:]   # Tasks after lunch
                ], ignore_index=True)
                return schedule

        earliest_lunch_start = max(lunch_window_start, schedule['End Time'].max())
        if earliest_lunch_start + lunch_duration <= work_end_time:
            schedule = pd.concat([
                schedule,
                pd.DataFrame([{'Task': 'Lunch Break', 'Start Time': earliest_lunch_start, 'End Time': earliest_lunch_start + lunch_duration, 'Priority Score': 'N/A'}])
            ], ignore_index=True)

    return schedule

# Create a daily schedule by allocating time slots for each task, including breaks
def create_schedule(tasks_df, work_start_time, work_end_time):
    schedule = []
    current_time = work_start_time
    short_break_duration = pd.Timedelta(minutes=15)  # 15 minutes break between tasks

    for index, task in tasks_df.iterrows():
        task_duration_minutes = task['Estimated Duration']
        if current_time + pd.Timedelta(minutes=task_duration_minutes) <= work_end_time:
            end_time = current_time + pd.Timedelta(minutes=task_duration_minutes)
            schedule.append({
                'Task': task['Task'],
                'Start Time': current_time,
                'End Time': end_time,
                'Priority Score': task['Priority Score']
            })
            current_time = end_time

            if current_time + short_break_duration <= work_end_time:
                break_start_time = current_time
                break_end_time = current_time + short_break_duration
                schedule.append({
                    'Task': 'Short Break',
                    'Start Time': break_start_time,
                    'End Time': break_end_time,
                    'Priority Score': 'N/A'
                })
                current_time = break_end_time

    schedule_df = pd.DataFrame(schedule)
    schedule_df = insert_lunch_break(schedule_df, work_start_time, work_end_time)
    schedule_df = schedule_df.sort_values(by='Start Time').reset_index(drop=True)
    return schedule_df

# Update the progress of tasks based on user input
def update_task_progress(tasks_df):
    print("\n--- Update Task Progress ---")
    for index, task in tasks_df.iterrows():
        print(f"Task: {task['Task']}, Current Progress: {task['Progress']} (1 to 10)")
        try:
            # Ask the user to update the progress for each task
            new_progress = int(input(f"Enter new progress for '{task['Task']}' (1 to 10) or leave blank to keep current: ") or task['Progress'])
            tasks_df.at[index, 'Progress'] = new_progress
        except ValueError:
            print(f"Invalid input for task '{task['Task']}'. Keeping current progress.")

    return tasks_df

# Save updated tasks with progress to the CSV file
def save_tasks_to_csv(tasks_df, file_path):
    tasks_df.to_csv(file_path, index=False)
    print(f"\nUpdated task progress saved to '{file_path}'.")

# Main function to run the scheduling script
def main():
    csv_file_path = 'tasks.csv'
    tasks_df = read_tasks(csv_file_path)

    if tasks_df is not None:
        tasks_df = calculate_priority_score(tasks_df)

        work_start_time_str = input("Enter your work start time (e.g., 9:00): ")
        work_end_time_str = input("Enter your work end time (e.g., 5:00): ")

        today_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        work_start_time = convert_to_timestamp(today_date, work_start_time_str, is_start_time=True)
        work_end_time = convert_to_timestamp(today_date, work_end_time_str, is_start_time=False)

        schedule_df = create_schedule(tasks_df, work_start_time, work_end_time)

        print("\n--- Daily Schedule with Breaks ---")
        print(schedule_df)

        # Update task progress based on user input
        tasks_df = update_task_progress(tasks_df)

        # Save updated task progress to the CSV file
        save_tasks_to_csv(tasks_df, csv_file_path)

        # Save the generated schedule to a CSV file
        schedule_df.to_csv('daily_schedule_with_breaks.csv', index=False)
        print("\nSchedule saved to 'daily_schedule_with_breaks.csv'.")

# Entry point of the script
if __name__ == '__main__':
    main()

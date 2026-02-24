from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load students data from Excel
def load_students():
    try:
        df = pd.read_excel('students.xlsx', header=0)
        # Rename columns to match expected format
        df.columns = ['Roll No', 'Student Name']
        # Skip the header row if it contains 'Roll No' as data
        df = df[df['Roll No'] != 'Roll No']
        # Convert Roll No to string for matching
        df['Roll No'] = df['Roll No'].astype(str)
        # Create dictionary with Roll No as key and Student Name as value
        students_dict = dict(zip(df['Roll No'], df['Student Name']))
        print(f"Loaded {len(students_dict)} students from Excel")
        return students_dict
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return {}

students_dict = load_students()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-total-students', methods=['GET'])
def get_total_students():
    """Return the total number of students from Excel"""
    return jsonify({'total': len(students_dict)})

@app.route('/api/download-attendance', methods=['GET'])
def download_attendance():
    """Download the Attendance.xlsx file"""
    try:
        return send_file('Attendance.xlsx', as_attachment=True, download_name='Attendance.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_attendance_excel(date_str, absent_rolls, od_rolls):
    """Update the Attendance.xlsx file with new attendance data"""
    try:
        # Read the Attendance.xlsx file
        df = pd.read_excel('Attendance.xlsx')
        
        # Get the student name to roll number mapping
        name_to_roll = {v: k for k, v in students_dict.items()}
        
        # Format date for column header (DD-MM-YYYY)
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        date_col = date_obj.strftime('%d-%m-%Y')
        
        # Find the column index for the date or add new column
        if date_col in df.columns:
            # Update existing date column
            col_idx = df.columns.get_loc(date_col)
        else:
            # Find the position before TOTAL column (column 34 usually)
            # Insert new column
            # Find where stats columns start
            total_col_idx = df.columns.get_loc('TOTAL')
            df.insert(total_col_idx, date_col, '')
            col_idx = total_col_idx
        
        # Get all student names (excluding summary rows)
        # The last 2 rows are "Total No. of PRESENT" and "Total No. of ABSENT"
        student_rows = df.iloc[:-2].copy()
        
        # Mark attendance for each student
        for idx, row in student_rows.iterrows():
            name = row['NAME']
            roll_no = name_to_roll.get(name)
            
            if roll_no:
                if roll_no in absent_rolls:
                    df.at[idx, date_col] = 'AB'
                elif roll_no in od_rolls:
                    df.at[idx, date_col] = 'OD'
                else:
                    df.at[idx, date_col] = 'P'
        
        # Calculate totals for the new column
        present_count = (df[date_col] == 'P').sum()
        absent_count = (df[date_col] == 'AB').sum()
        
        # Update the TOTAL row (second to last row)
        total_row_idx = len(df) - 2
        df.at[total_row_idx, date_col] = present_count
        
        # Update the ABSENT row (last row)
        absent_row_idx = len(df) - 1
        df.at[absent_row_idx, date_col] = absent_count
        
        # Recalculate TOTAL, P, OD, TOTAL.1, PERCENTAGE for each student
        # Find date columns (columns between NAME and TOTAL)
        name_idx = df.columns.get_loc('NAME')
        total_idx = df.columns.get_loc('TOTAL')
        date_cols = df.columns[name_idx+1:total_idx]
        
        # Update TOTAL, P, OD columns for each student
        for idx in range(len(df) - 2):  # Exclude summary rows
            total_days = 0
            present_days = 0
            od_days = 0
            
            for col in date_cols:
                val = df.at[idx, col]
                if val in ['P', 'AB', 'OD']:
                    total_days += 1
                    if val == 'P':
                        present_days += 1
                    elif val == 'OD':
                        od_days += 1
            
            df.at[idx, 'TOTAL'] = total_days
            df.at[idx, 'P'] = present_days
            df.at[idx, 'OD'] = od_days
            df.at[idx, 'TOTAL.1'] = present_days + od_days
            
            # Calculate percentage
            if total_days > 0:
                percentage = round(((present_days + od_days) / total_days) * 100, 2)
                df.at[idx, 'PERCENTAGE'] = percentage
        
        # Save the updated Excel file
        df.to_excel('Attendance.xlsx', index=False)
        print(f"Updated Attendance.xlsx with date {date_col}")
        return True
    except Exception as e:
        print(f"Error updating Attendance.xlsx: {e}")
        return False

@app.route('/api/process-attendance', methods=['POST'])
def process_attendance():
    try:
        data = request.json
        
        # Extract form data
        date = data.get('date', '')
        hour = data.get('hour', '')
        department = data.get('department', 'II YEAR - A')
        course = data.get('course', 'B.Tech IT')
        # Use dynamic total from Excel if not provided
        total_students = int(data.get('totalStudents', len(students_dict)))
        
        # Parse absent and OD roll numbers
        absent_input = data.get('absent', '').strip()
        od_input = data.get('od', '').strip()
        
        # Sort roll numbers in ascending order (numerically)
        absent_rolls = sorted([r.strip() for r in absent_input.split(',') if r.strip()], key=int)
        od_rolls = sorted([r.strip() for r in od_input.split(',') if r.strip()], key=int)
        
        # Validation: Check for empty input
        if not absent_input and not od_input:
            return jsonify({'error': 'Please enter at least one absent or OD roll number'}), 400
        
        # Validation: Check for numeric roll numbers
        for roll in absent_rolls:
            if not roll.isdigit():
                return jsonify({'error': f'Roll number "{roll}" must be numeric'}), 400
        
        for roll in od_rolls:
            if not roll.isdigit():
                return jsonify({'error': f'Roll number "{roll}" must be numeric'}), 400
        
        # Validation: Check for duplicates within absent
        if len(absent_rolls) != len(set(absent_rolls)):
            return jsonify({'error': 'Duplicate roll numbers in Absent list'}), 400
        
        # Validation: Check for duplicates within OD
        if len(od_rolls) != len(set(od_rolls)):
            return jsonify({'error': 'Duplicate roll numbers in OD list'}), 400
        
        # Validation: Check if roll numbers exist in both absent and OD
        common_rolls = set(absent_rolls) & set(od_rolls)
        if common_rolls:
            return jsonify({'error': f'Roll number(s) {", ".join(common_rolls)} cannot be both Absent and OD'}), 400
        
        # Calculate attendance
        absent_count = len(absent_rolls)
        od_count = len(od_rolls)
        present_count = total_students - absent_count
        
        # Percentage calculation (OD counted as present)
        percentage = round((present_count / total_students) * 100, 2)
        
        # Get student names for absent list (already sorted)
        absentees_list = []
        warnings = []
        for roll in absent_rolls:
            if roll in students_dict:
                absentees_list.append(f"{students_dict[roll]} ({roll})")
            else:
                absentees_list.append(f"Unknown Student ({roll})")
                warnings.append(f'Roll number {roll} not found in Excel')
        
        # Get student names for OD list (already sorted)
        od_list = []
        for roll in od_rolls:
            if roll in students_dict:
                od_list.append(f"{students_dict[roll]} ({roll})")
            else:
                od_list.append(f"Unknown Student ({roll})")
                warnings.append(f'Roll number {roll} not found in Excel')
        
        # Generate report
        report = f"""Good morning sir,

Date : {date}
Hour: {hour}

II YEAR - A
{course}  : {present_count}/{total_students}
--------------------------------
Percentage : {percentage}%

Absentees List
"""
        for i, name in enumerate(absentees_list, 1):
            report += f"{i}. {name}\n"
        
        report += "\nOD\n"
        for i, name in enumerate(od_list, 1):
            report += f"{i}. {name}\n"
        
        report += "\nThank you sir"
        
        # Update Attendance.xlsx
        save_to_excel = data.get('saveToExcel', True)
        if save_to_excel and date:
            update_attendance_excel(date, absent_rolls, od_rolls)
        
        return jsonify({
            'report': report,
            'percentage': percentage,
            'present': present_count,
            'absent': absent_count,
            'od': od_count,
            'total': total_students,
            'warnings': warnings,
            'excelUpdated': save_to_excel
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

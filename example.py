#teacher example of a basic BD application

import psycopg2

def get_option():
    option=-1

    while (option not in [0,1,2,3,4,5,6]):
        print('1 - List Departments')
        print('2 - List Employees')
        print('3 - Get Employee')
        print('4 - Add Employee')
        print('5 - Remove Employee')
        print('6 - Move Employee to Department')
        print('0 - Exit')

        try:
            option=int(input('Option: '))
        except:
            option=-1

    return option

def connect_db():
    connection = psycopg2.connect(user = "empuser",
        password = "empuser",   # password should not be visible - will address this later on the course
        host = "localhost",
        port = "5432",
        database = "empdb")
    # parameters should be changable - will adress this later on the course

    return connection

def list_departments():
    print('--- List of Departments ---')

    connection=connect_db()
    cursor = connection.cursor()
    cursor.execute('select * from departments')

    for row in cursor:
        print(row[0],'\t',row[1],'\t',row[2])

    print('---------------------------\n')

    return

def list_employees():
    print('\n--- List of Employees ---')

    ## To Be Completed

    print('-------------------------\n')

def get_employee():
    print('\n--- Get Employee ---')

    name=''
    while (len(name)==0):
        name=input('Name: ')

    connection=connect_db()
    cursor = connection.cursor()
    cursor.execute("select emp_no, employees.name, job, date_contract, salary, commissions, departments.name \
    from employees,departments \
    where departments_dep_no = dep_no \
    and employees.name='"+name+"'")

    # and employees.name='' or 1=1 --'

    # cursor.execute("select emp_no, employees.name, job, date_contract, salary, commissions, departments.name \
    # from employees,departments \
    # where departments_dep_no = dep_no \
    # and employees.name=%s",(name,))

    if (cursor.rowcount==0):
        print('Employee does not exist!')

    for row in cursor:
        print('No:',row[0])
        print('Name:',row[1])
        print('Job:',row[2])
        print('Date Contract:',row[3])
        print('Salary:',row[4])
        print('Commissions:',row[5])
        print('Department:',row[6])

    print('--------------------\n')

def add_employee():
    print('\n--- Add Employee ---')

    ## To Be Completed

    print('--------------------\n')

def remove_employee():
    print('\n--- Remove Employee ---')

    name=''
    while (len(name)==0):
        name=input('Name: ')

    connection=connect_db()
    cursor = connection.cursor()
    cursor.execute("delete from employees \
    where name=%s",(name,))

    if (cursor.rowcount==0):
        print('Employee does not exist!')
    else:
        print(cursor.rowcount, 'employee(s) deleted!')
        connection.commit()

    print('-----------------------\n')

def move_emp_department():
    print('\n--- Move Employee to Department ---')

    ## To Be Completed

    print('-----------------------------------\n')


if __name__ == '__main__':
    function_list = (list_departments, list_employees, get_employee, add_employee, remove_employee, move_emp_department)
    option = -1

    while (option!=0):
        option = get_option()
        if (option != 0):
            function_list[option-1]()

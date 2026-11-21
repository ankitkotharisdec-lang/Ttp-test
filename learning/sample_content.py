"""Original sample lessons (Python for data engineering). Used by the seed command, the SQLite seed migration,
and to generate the Supabase seed data. Each lesson is a list of blocks; admins edit/extend these in the admin panel."""


def T(body, title=''):
    return dict(block_type='text', title=title, body=body)


def M(body, title='Must Know:'):
    return dict(block_type='must_know', title=title, body=body)


def H(body):
    return dict(block_type='highlight', body=body)


def C(code, title='', body=''):
    return dict(block_type='code', title=title, body=body, code=code)


def E(title, question, options, correct, explanation):
    return dict(block_type='example', title=title, body=question, options='\n'.join(options), correct_option=correct, explanation=explanation)


def S(body, title='Key takeaways'):
    return dict(block_type='summary', title=title, body=body)


SAMPLE_BLOCKS = {
    'What is Python?': [
        T('Python is a general-purpose programming language known for code that reads almost like plain English. In data engineering it is the glue of the job: you use it to pull data from APIs and files, clean it, and load it into databases and warehouses.'),
        M('Python is easy to read, so it is quick to learn and easy for a whole team to maintain.'),
        T('Here is why data engineers reach for Python first:\n\n- Libraries for every job: pandas for tables, requests for APIs, SQLAlchemy for databases.\n- It runs everywhere: laptops, servers, Airflow pipelines and cloud functions.\n- A huge community: almost every error message already has an answer online.'),
        H('You do not need to memorise everything. You need to know what is possible and how to look things up.'),
        E('Example 1', 'Which task is Python commonly used for in data engineering?',
          ['Cleaning a CSV file before loading it into a database', 'Editing photos by hand', 'Designing a company logo', 'Printing paper reports manually'], 1,
          'Python automates data work such as cleaning files, calling APIs and loading results into databases.'),
        S('Python is readable, widely used, and the everyday glue language of data engineering.'),
    ],
    'Installing Python': [
        T('Before you write code you need Python on your computer. First check whether it is already installed: open a terminal and run the command below.'),
        C('python --version', title='Check your version', body='You should see something like Python 3.12.x.'),
        M('Always use Python 3. Python 2 is retired and no longer receives updates.'),
        E('Example 1', 'Which version of Python should you install for new projects?',
          ['Python 3 (the latest stable release)', 'Python 2.7', 'Any version older than 3.5', 'It does not matter'], 1,
          'Python 3 is the only supported line. Python 2 stopped receiving updates in 2020.'),
        T('On some systems the command is python3 instead of python. Both mean the same thing here.'),
        H('Use one virtual environment per project so libraries from one project never break another.'),
        C('python -m venv .venv\nsource .venv/bin/activate   # on Windows: .venv\\Scripts\\activate', title='Create a virtual environment',
          body='A virtual environment is a private folder of libraries for a single project.'),
        S('Check your version with python --version, install Python 3, and create a virtual environment for every project.'),
    ],
    'Your first program': [
        T('Every programmer starts with the same tiny program: make the computer say something. In Python that is one line.'),
        C('print("Hello, data engineering!")', title='Your first program', body='Save this in a file called hello.py and run it with python hello.py.'),
        M('print() shows a value on the screen. Text goes inside quotes.'),
        T('print() can also do maths. Python works out the answer first and then prints it.'),
        C('print(2 + 3)', title='Printing a calculation'),
        E('Example 1', 'What does print(2 + 3) show on the screen?', ['5', '23', '2 + 3', 'An error'], 1,
          'Python calculates 2 + 3 first, so the number 5 is printed. Without quotes it is maths, not text.'),
        H('If you get an error, read the last line first. It usually tells you exactly what went wrong.'),
        S('print() shows values. Quotes make text. Without quotes, Python calculates.'),
    ],
    'Understanding variables': [
        T('A variable is a name that points to a value. Think of the column names in a spreadsheet: each name stands for the values stored under it. In a pipeline you use variables to hold things like file names and row counts.'),
        C('rows_loaded = 1500\nsource = "orders.csv"\nprint(source, rows_loaded)', title='Creating variables', body='The name goes on the left of =, the value on the right.'),
        M('Use = to assign a value to a name. It means "store this", not "is equal to".'),
        H('Choose names that explain themselves: rows_loaded is better than x.'),
        T('Rules for variable names:\n\n- Use letters, numbers and underscores.\n- Never start with a number.\n- Names are case-sensitive: Rows and rows are different variables.\n- By convention, use snake_case such as total_rows.'),
        E('Example 1', 'Which one is a valid variable name?', ['total_rows', '2nd_file', 'row-count', 'class name'], 1,
          'total_rows uses only letters and underscores. 2nd_file starts with a number, row-count has a hyphen, and class name has a space.'),
        E('Example 2', 'After these lines run, what is count?\n\ncount = 10\ncount = count + 5', ['15', '10', '5', '105'], 1,
          'count starts at 10. The second line reads the old value, adds 5, and stores 15 back into count.'),
        S('A variable is a named value. Use clear snake_case names and = to assign.'),
    ],
    'Numbers and strings': [
        T('The two kinds of values you will use most are numbers and strings (text). Python picks the type automatically from how you write the value.'),
        C('file_size_mb = 12.5      # float: a decimal number\nrow_count = 2400         # int: a whole number\ntable_name = "orders"    # str: text in quotes\nprint(table_name + " has " + str(row_count) + " rows")', title='Three common types'),
        M('Use int for whole numbers, float for decimals, and str for text in quotes.'),
        T('You can only join text with text. To put a number inside a sentence, convert it with str(), as the last line above does. The function len() counts how many characters a string has.'),
        C('print(len("data"))', title='Counting characters'),
        E('Example 1', 'What is the type of the value 3.14?', ['float', 'int', 'str', 'bool'], 1,
          'A number with a decimal point is a float.'),
        E('Example 2', 'What does print(len("data")) show?', ['4', '3', '5', 'An error'], 1,
          'The word data has four characters, so len returns 4.'),
        H('If you see "can only concatenate str", you tried to join text and a number. Convert the number with str().'),
        S('Numbers are int or float, text is str. Use str() to convert a number into text and len() to count characters.'),
    ],
}


def seed_blocks(Lesson, LessonBlock):
    """Add the sample blocks to lessons of the 'python' course that have none yet. Returns how many lessons were filled."""
    filled = 0
    for title, blocks in SAMPLE_BLOCKS.items():
        lesson = Lesson.objects.filter(title=title, chapter__section__course__slug='python').first()
        if lesson is None or LessonBlock.objects.filter(lesson=lesson).exists():
            continue
        for pos, b in enumerate(blocks, 1):
            LessonBlock.objects.create(lesson=lesson, position=pos, is_published=True, **b)
        filled += 1
    return filled

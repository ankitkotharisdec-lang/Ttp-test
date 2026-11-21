from django.core.management.base import BaseCommand
from django.db import transaction
from learning.models import Course,Section,Chapter,Lesson,LessonBlock
from learning.sample_content import seed_blocks
DATA={
 'Python Core': [('Introduction to Python',['What is Python?','Installing Python','Your first program']),('Variables and Data Types',['Understanding variables','Numbers and strings','Type conversion']),('Control Flow',['If statements','Else and elif','Nested conditions']),('Strings',['Indexing','Slicing','String methods']),('Loops and Iteration',['For loops','While loops','Break and continue'])],
 'Data Structures':[('Lists and Tuples',['Creating lists','List methods','Tuples']),('Dictionaries and Sets',['Key-value pairs','Dictionary methods','Sets'])],
 'OOP and Modules':[('Functions',['Defining functions','Arguments','Return values']),('Classes and Objects',['Classes','Objects','Methods'])],
 'Projects':[('Expense Tracker',['Project requirements','Build the tracker','Test your solution'])]}
class Command(BaseCommand):
    help='Add sample Python curriculum without overwriting existing edits'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        course,_=Course.objects.get_or_create(slug='python',defaults={'title':'Python','is_published':True})
        for si,(name,chapters) in enumerate(DATA.items(),1):
            section,_=Section.objects.get_or_create(course=course,title=name,defaults={'position':si,'is_published':True})
            for ci,(title,lessons) in enumerate(chapters,1):
                chapter,_=Chapter.objects.get_or_create(section=section,title=title,defaults={'position':ci,'is_published':True})
                for li,title in enumerate(lessons,1):
                    Lesson.objects.get_or_create(chapter=chapter,title=title,defaults={'position':li,'is_published':True,'explanation':'Sample lesson. Replace this text through the Django admin.','code_example':'message = "Hello, Python!"\nprint(message)','expected_output':'Hello, Python!','summary':'Practice the example, then add your own content.'})
        seed_blocks(Lesson,LessonBlock)
        self.stdout.write(self.style.SUCCESS('Sample Python curriculum ready.'))

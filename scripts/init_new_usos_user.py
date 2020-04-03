import sys
from pathlib import Path
from argparse import ArgumentParser
from dotenv import load_dotenv

from db.db_connector import DbConnector

from usos.api_calls import get_user_courses, get_user_usos_id_and_name, get_user_programs, get_user_points
from usos.db.update_tables import update_usos_programs, update_usos_courses, update_new_usos_points
from usos.db.user_ops import get_usos_users

from logger.log import Log

if __name__ == '__main__':
    # Parse args
    argparser = ArgumentParser(
        description='Get user USOS ID, first and last name from USOS and fill `users` table in DB'
    )
    argparser.add_argument(
        'user_ids', type=int, metavar='UIDs', nargs='+',
        help='User IDs from `users` table'
    )
    args = argparser.parse_args()

    # Load .env
    env_path = Path(__file__).parents[1] / '.env'
    load_dotenv(dotenv_path=env_path)

    Log.usos().info('Started init new usos user script with UIDs: %s', ', '.join([str(x) for x in args.user_ids]))

    # Get users from DB
    users = get_usos_users(args.user_ids)
    if len(users) != len(args.user_ids):
        Log.usos().error('Attempt to update user that doesn\'t exist')
        sys.exit(-1)

    users_courses = {}  # Dictionary that holds each user as keys and their courses as values
    # Fetch and update programs and courses
    Log.usos().debug('Fetching and updating programs and courses:')
    for user in users:
        Log.usos().debug('User %s %s [%s]:', user.fb_first_name, user.fb_last_name, user.id)
        Log.usos().debug('Fetching programs...')
        programs = get_user_programs(user)
        for program in programs:
            Log.usos().debug('--> [%s] %s', program.program_id, program.short_program_name_pl)
        Log.usos().debug('Updating DB...')
        update_usos_programs(programs)

        Log.usos().debug('Fetching courses...')
        courses = get_user_courses(user)
        users_courses[user] = courses
        for course in courses:
            Log.usos().debug('--> [%s] %s', course.course_id, course.course_name_pl)
        Log.usos().debug('Updating DB...')
        update_usos_courses(courses)
    Log.usos().info('Fetched programs and courses for given users.')

    # Getting course IDs from DB
    connection = DbConnector().get_connection()
    cursor = connection.cursor()

    Log.usos().debug('Getting course IDs from DB...')
    query_course_ids = 'select course_id, id from usos_courses;'
    cursor.execute(query_course_ids)

    course_ids = {course_id: str(tbl_id) for (course_id, tbl_id) in cursor}

    # Updating USOS information and fetching and updating points
    Log.usos().debug('Filling USOS information for following users:')
    for user in users:
        Log.usos().debug('User %s %s [%s]:', user.fb_first_name, user.fb_last_name, user.id)

        usos_info = get_user_usos_id_and_name(user)
        Log.usos().debug('USOS info:')
        Log.usos().debug('--> USOS ID: %s', usos_info['id'])
        Log.usos().debug('--> First name: %s', usos_info['first_name'])
        Log.usos().debug('--> Last name: %s', usos_info['last_name'])

        query_course_ids = 'select id from usos_courses'

        insert_usos_info = 'update users ' \
                           'set usos_id = %s, usos_first_name = %s, usos_last_name = %s, usos_courses = %s ' \
                           'where id = %s;'

        Log.usos().debug('Updating user\'s record in database...')
        cursor.execute(insert_usos_info, (
            usos_info['id'], usos_info['first_name'], usos_info['last_name'],
            ';'.join(sorted([course_ids[c.course_id] for c in users_courses[user]])), user.id
        ))
        connection.commit()

        Log.usos().debug('Fetching points...')
        points = get_user_points(user, False)
        Log.usos().debug('Updating DB...')
        update_new_usos_points(points)

        Log.usos().info('Updated user USOS info and points: %s %s [%s]', user.fb_first_name, user.fb_last_name,
                        user.id)

    cursor.close()

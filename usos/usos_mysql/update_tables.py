from db.db_connector import DBConnector


def update_usos_courses(courses: set, connector: DBConnector):
    """Update `usos_courses` table

    :param courses: Set of usos courses
    :param connector: MySQL DB connector
    """
    columns = [
        'course_id', 'course_name_pl',
        'course_name_en', 'term_id'
    ]
    generic_update_table(
        objects=courses,
        table_name='usos_courses',
        columns=columns,
        obj_pkey=lambda c: c.course_id,
        obj_to_tuple=lambda c: (
            c.course_id, c.course_name_pl,
            c.course_name_en, c.term_id
        ),
        connector=connector
    )


def update_usos_programs(programs: set, connector: DBConnector):
    """Update `usos_programs` table

    :param programs: Set of usos programs
    :param connector: MySQL DB connector
    """
    columns = [
        'program_id', 'program_name_pl', 'short_program_name_pl',
        'program_name_en', 'short_program_name_en'
    ]
    generic_update_table(
        objects=programs,
        table_name='usos_programs',
        columns=columns,
        obj_pkey=lambda p: p.program_id,
        obj_to_tuple=lambda p: (
            p.program_id, p.program_name_pl, p.short_program_name_pl,
            p.program_name_en, p.short_program_name_en
        ),
        connector=connector
    )


def update_usos_points(points: set, connector: DBConnector):
    """Update `usos_points` table

    :param points: Set of user points
    :param connector: MySQL DB connector
    """
    columns = [
        'node_id', 'name', 'points', 'comment',
        'grader_id', 'student_id', 'last_changed', 'course_id'
    ]
    generic_update_table(
        objects=points,
        table_name='usos_points',
        columns=columns,
        obj_pkey=lambda p: p.node_id,
        obj_to_tuple=lambda p: (
            p.node_id, p.name, p.points, p.comment,
            p.grader_id, p.student_id, p.last_changed, p.course_id
        ),
        connector=connector
    )


def generic_update_table(objects: set, table_name: str, columns: list, obj_pkey, obj_to_tuple, connector: DBConnector):
    """Generic function to update tables in database

    It searches for objects that aren't in the table yet and inserts them respectively.

    :param objects: Objects to be inserted
    :param table_name: Table name that we want to insert records
    :param columns: List of columns we want to instert. First element should be primary key column name
    :param obj_pkey: Function that extracts primary key (unique) attribute from object
    For example: lambda x: x.some_primary_key_attribute
    :type obj_pkey: function
    :param obj_to_tuple: Function that converts object to tuple. Returned tuple should have the same length
    as `columns` parameter and have attributes in the same order.
    For example: if `columns` is defined as ['pkey', 'name', 'other_attr'], it should look something like this:
    lambda x: (x.pkey, x.name, x.other_attr)
    :type obj_to_tuple: function
    :param connector: MySQL DB Connector
    """
    cursor = connector.connection.cursor()
    get_pkeys_query = 'select {} from {};'.format(columns[0], table_name)
    cursor.execute(get_pkeys_query)

    pkeys = {i for (i,) in cursor}
    insert_data = []
    for obj in objects:
        if obj_pkey(obj) not in pkeys:
            insert_data.append(obj_to_tuple(obj))

    if len(insert_data) == 0:
        return

    insert_new_data = 'insert into {} ({}) values ({});'.format(
        table_name, ', '.join(columns), ', '.join(['%s' for i in range(len(columns))])
    )

    cursor.executemany(insert_new_data, insert_data)
    connector.connection.commit()
    cursor.close()

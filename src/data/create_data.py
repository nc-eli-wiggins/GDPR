import pandas as pd
import numpy as np

from faker import Faker

fake = Faker()

num_entries = 12000  

data = {
    'User ID': [i + 1001 for i in range(num_entries)],
    'Name': [fake.name() for _ in range(num_entries)],
    'Graduation Date': [fake.date_between(start_date='-5y', end_date='today') for _ in range(num_entries)],
    'Email Address': [fake.email() for _ in range(num_entries)],
    'Course': [fake.word() + " Studies" for _ in range(num_entries)],
    'Town': [fake.city() for _ in range(num_entries)],
    'Sex': [np.random.choice(['Male', 'Female']) for _ in range(num_entries)],
    'DOB': [fake.date_of_birth(minimum_age=18, maximum_age=30) for _ in range(num_entries)],
}

df = pd.DataFrame(data)

df.to_csv('dummy_data_large.csv', index=False)


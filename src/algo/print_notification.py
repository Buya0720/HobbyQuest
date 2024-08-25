import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import seaborn as sns; sns.set()
import warnings

# Ignore specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# Load the original CSV files
df = pd.read_csv('fake_user_data_scarce.csv')  #user data
df_events = pd.read_csv('sydney_events_updated.csv') #events data
df_notifications = pd.read_csv('duolingo_style_fun_name_notifications_with_time.csv') #notifications data

# Define optimal number of geographical clusters
K_clusters = range(1, 20)
kmeans = [KMeans(n_clusters=i) for i in K_clusters]
Y_axis = df[['Latitude']]
X_axis = df[['Longitude']]
score = [kmeans[i].fit(Y_axis).score(Y_axis) for i in range(len(kmeans))]

# Find the optimal number of clusters where the score is larger than the threshold (-0.15)
threshold = -0.15
k_optimal = next((i + 1 for i, s in enumerate(score) if s > threshold), None)

# Clustering using K-Means with the optimal number of clusters
kmeans = KMeans(n_clusters=k_optimal, init='k-means++')
kmeans.fit(df[['Latitude', 'Longitude']])  # Use the correct columns from df

# Assign the clusters to the DataFrame
df['Cluster'] = kmeans.predict(df[['Latitude', 'Longitude']])

# Predict the clusters for the events data using the same model
df_events['Cluster'] = kmeans.predict(df_events[['Latitude', 'Longitude']])

# making a list from data frame column headings
interest_columns = df.columns[4:34].tolist()

# Create a DataFrame that shows the binary representation and position for each interest
interest_binary_df = pd.DataFrame(columns=['Interest', 'Binary', 'Position'])

# Fill the DataFrame with interest names, their corresponding binary positions, and position numbers
for i, interest in enumerate(interest_columns):
    binary_string = ''.join(['1' if j == i else '0' for j in range(len(interest_columns))])
    position_number = i + 1  # Position starts from 1
    interest_binary_df = pd.concat([interest_binary_df, pd.DataFrame({'Interest': [interest], 'Binary': [binary_string], 'Position': [position_number]})], ignore_index=True)

# Convert interests to binary string
df['Interests'] = df[interest_columns].apply(lambda row: ''.join(row.astype(int).astype(str)), axis=1)

# convert hourly availability to binary string
def hours_to_binary(row, day):
    return ''.join(row[[f'{day}_hour_{i}' for i in range(24)]].astype(int).astype(str))

# Convert availability for each day to binary
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
    df[day] = df.apply(lambda row: hours_to_binary(row, day), axis=1)

# Select columns for the optimized DataFrame
columns_to_keep = ['UserID', 'Name', 'Latitude', 'Longitude', 'Cluster', 'Interests', 
                   'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Create the optimized DataFrame
df_optimized = df[columns_to_keep].copy()  # Ensure it's a copy

# Initialize a list to store the subgroups
subgroups = []

#  total number of clusters
total_clusters = len(df_optimized['Cluster'].unique())
cluster_iteration = 0

# global counter for SubgroupID
subgroup_id_counter = 1

# Generate Subgroups (based on location, interest etc.)
def generate_subgroups(cluster_df, cluster_id): #cluster_df : data for a specific geographical cluster
    global cluster_iteration, subgroup_id_counter
    cluster_iteration += 1
    #print(f"Processing Cluster {cluster_iteration} of {total_clusters} (Cluster ID: {cluster_id})")

    # Iterate over each interest within the cluster and filter users based on interest
    for interest_index, interest in enumerate(interest_columns, start=1):
        interested_users = cluster_df[cluster_df['Interests'].apply(lambda x: x[interest_index-1] == '1')]

        if len(interested_users) >= 2:
            # Group by weekday availability
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                available_users = interested_users[interested_users[day].apply(lambda x: '1' in x)]

                if len(available_users) >= 2:
                    # Group by timeslot (hour of the day) availability
                    for hour in range(24):
                        hour_available_users = available_users[available_users[day].apply(lambda x: x[hour] == '1')]
                    
                        if len(hour_available_users) >= 2:
                            # if there are minimum 2 people available reate the subgroup with a unique ID
                            subgroup = {
                                'SubgroupID': subgroup_id_counter,
                                'GeoCluster': cluster_id,
                                'Interest': interest_index,
                                'Day': day,
                                'Hour': hour,
                                'Users': ','.join(map(str, hour_available_users['UserID'].tolist())),
                                'Size': len(hour_available_users)
                            }
                            subgroups.append(subgroup)
                            #print(f"  Subgroup found: SubgroupID {subgroup_id_counter}, Cluster {cluster_id}, Interest {interest_index}/{len(interest_columns)}, Day {day}, Hour {hour}, Size {len(hour_available_users)}")
                            
                            # Increment the SubgroupID counter
                            subgroup_id_counter += 1

# Generate subgroups for each geographic cluster
for cluster_id, cluster_df in df_optimized.groupby('Cluster'):
    generate_subgroups(cluster_df, cluster_id)
    
# Merge subgroups with events based on matching 'Interest' and 'Cluster'
df_events = pd.merge(df_events, interest_binary_df[['Interest', 'Position']], on='Interest', how='left')
subgroups_df = pd.DataFrame(subgroups)

merged_df = pd.merge(subgroups_df, df_events, left_on=['GeoCluster', 'Interest'], right_on=['Cluster', 'Position'], how='inner')

# Filter the merged DataFrame for valid matches
valid_matches = merged_df[(merged_df['Size'] >= merged_df['MinPeople']) & (merged_df['Size'] <= merged_df['MaxPeople'])].copy()  # Ensure it's a copy

# Create 'Event_Subgroup_ID' for each valid match
valid_matches.loc[:, 'Event_Subgroup_ID'] = valid_matches.apply(
    lambda row: f"Event_{row['EventID']}_Subgroup_{row['SubgroupID']}", axis=1
)

# Explode the 'Users' column to get each user in a separate row
exploded_valid_matches = valid_matches.assign(Users=valid_matches['Users'].str.split(',')).explode('Users')

# Track the number of participants for each Event_Subgroup_ID
event_participant_count = exploded_valid_matches.groupby('Event_Subgroup_ID')['Users'].count().to_dict()

# Create a DataFrame to track user assignments
user_event_assignments = pd.DataFrame(columns=['UserID', 'Event_Subgroup_ID', 'Number_of_Participants'])

# Assign users to event subgroups ensuring both minimum and maximum participation is met
for user_id, group in exploded_valid_matches.groupby('Users'):
    assigned_events = 0
    
    for _, row in group.iterrows():
        event_subgroup_id = row['Event_Subgroup_ID']
        min_people = row['MinPeople']
        max_people = row['MaxPeople']
        
        # Check if the current number of participants is within the allowed range
        if assigned_events < 2 and event_participant_count[event_subgroup_id] >= min_people and event_participant_count[event_subgroup_id] < max_people:
            # Assign the user to this event subgroup and record the number of participants
            user_event_assignments = pd.concat([
                user_event_assignments,
                pd.DataFrame({
                    'UserID': [user_id],
                    'Event_Subgroup_ID': [event_subgroup_id],
                    'Number_of_Participants': [event_participant_count[event_subgroup_id]]
                })
            ], ignore_index=True)
            
            # Update the participant count for this Event_Subgroup_ID
            event_participant_count[event_subgroup_id] += 1
            assigned_events += 1

# Ensure that all event subgroups meet the minimum and do not exceed the maximum participation requirement
final_user_event_assignments = user_event_assignments.groupby('Event_Subgroup_ID').filter(
    lambda x: len(x) >= valid_matches['MinPeople'].min() and len(x) <= valid_matches['MaxPeople'].max()
)

# Extract SubgroupID from Event_Subgroup_ID
final_user_event_assignments.loc[:, 'SubgroupID'] = final_user_event_assignments['Event_Subgroup_ID'].apply(lambda x: int(x.split('_')[3]))

# Merge subgroups_df with final_user_event_assignments to get Day and Hour
final_user_event_assignments = pd.merge(final_user_event_assignments, subgroups_df[['SubgroupID', 'Day', 'Hour']], on='SubgroupID', how='left')

# Extract Day and Time Information
def format_event_time(day, hour):
    if 0 <= hour < 12:
        period = 'Morning'
    elif 12 <= hour < 18:
        period = 'Afternoon'
    else:
        period = 'Night'
    return f"{day} {period}"

final_user_event_assignments.loc[:, 'EventTime'] = final_user_event_assignments.apply(
    lambda row: format_event_time(row['Day'], row['Hour']), axis=1
)

#  Merge final_user_event_assignments with df_notifications based on EventID extracted from Event_Subgroup_ID
final_user_event_assignments['EventID'] = final_user_event_assignments['Event_Subgroup_ID'].apply(lambda x: int(x.split('_')[1]))

merged_df = pd.merge(final_user_event_assignments, df_notifications, left_on='EventID', right_on='EventID', how='left')

# Replace the {EventTime} placeholder with the actual EventTime
merged_df.loc[:, 'Message'] = merged_df.apply(
    lambda row: row['Message'].replace('{EventTime}', row['EventTime']), axis=1
)

#  Select relevant columns and format the final output
final_notification_df = merged_df[['UserID', 'Event_Subgroup_ID', 'FunName', 'Location', 'EventTime', 'Message']]

# Ask for UserID
user_id = int(input("Enter UserID: "))

# Filter notifications for the specified UserID
#user_notifications = final_notification_df[final_notification_df['UserID'] == int(user_id)]
user_notifications = final_notification_df[final_notification_df['UserID'].astype(int) == int(user_id)]
final_notification_df['UserID'] = final_notification_df['UserID'].astype(str).str.strip()

# Print notifications for the specified UserID
if not user_notifications.empty:
    random_notification = user_notifications['Message'].sample(n=1).iloc[0]
    print(random_notification)
else:
    print("No notifications found for UserID", user_id)

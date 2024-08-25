import pandas as pd
from sklearn.cluster import KMeans
import warnings

# Suppress arnings
warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# Load the data used in the function
df = pd.read_csv('fake_user_data_scarce.csv')
df_events = pd.read_csv('sydney_events_updated.csv')
df_notifications = pd.read_csv('duolingo_style_fun_name_notifications_with_time.csv')

def add_user_to_database(df, df_events):
    # Create a new user DataFrame with the same columns as df
    new_user = pd.DataFrame(columns=df.columns)
    
    # Identify columns of interest
    interest_columns = [col for col in df.columns if col not in ['UserID', 'Name', 'Latitude', 'Longitude', 'Cluster', 'JobCategory'] and not col.startswith(('Monday_', 'Tuesday_', 'Wednesday_', 'Thursday_', 'Friday_', 'Saturday_', 'Sunday_'))]
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print("Please answer the following questions to add a new user:")
    
    # Get user information
    new_user.at[0, 'UserID'] = df['UserID'].max() + 1
    new_user.at[0, 'Name'] = input("Enter your name: ")
    new_user.at[0, 'Latitude'] = float(input("Enter your latitude: "))
    new_user.at[0, 'Longitude'] = float(input("Enter your longitude: "))
    
    # Get interests
    for interest in interest_columns:
        response = input(f"Are you interested in {interest}? (yes/no): ").lower()
        new_user.at[0, interest] = 1 if response == 'yes' else 0
    
    # Get availability
    for day in days:
        hours = input(f"Enter the hours you're available on {day} (comma-separated, e.g., 1,2,3,15,16): ")
        for hour in range(24):
            new_user.at[0, f'{day}_hour_{hour}'] = 0
        for hour in hours.split(','):
            if hour.isdigit():
                new_user.at[0, f'{day}_hour_{int(hour)-1}'] = 1

    # Finding the best number of Cluster for K nearest neighbour by defining a range and use thershold
    K_clusters = range(1, 20)
    kmeans_models = [KMeans(n_clusters=i) for i in K_clusters]
    score = [kmeans_models[i].fit(df[['Latitude', 'Longitude']]).score(df[['Latitude', 'Longitude']]) for i in range(len(kmeans_models))]

    # Define a threshold for clustering optimization using elbow method
    threshold = -0.15
    k_optimal = next((i + 1 for i, s in enumerate(score) if s > threshold), 5)  # Default to 5 clusters if no optimal found

    # Apply KMeans clustering with the optimal number of clusters
    kmeans = KMeans(n_clusters=k_optimal, init='k-means++')
    df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])
    
    # Predict cluster for the new user
    new_user['Cluster'] = kmeans.predict(new_user[['Latitude', 'Longitude']])
    
    # Convert interests to binary string
    new_user['Interests'] = new_user[interest_columns].apply(lambda row: ''.join(row.astype(int).astype(str)), axis=1)
    
    # Convert availability for each day to binary
    for day in days:
        new_user[day] = new_user[[f'{day}_hour_{i}' for i in range(24)]].apply(lambda row: ''.join(row.astype(int).astype(str)), axis=1)
    
    # Add the new user to the main DataFrame
    df = pd.concat([df, new_user], ignore_index=True)
    
    return df

new_user_df = add_user_to_database(df, df_events)
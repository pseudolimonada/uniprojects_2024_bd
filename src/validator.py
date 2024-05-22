from utils import StatusCodes, UserDetails, logger

# checks if user_type is a key in UserDetails
def user_type(user_type: str) -> bool:
    for user in UserDetails.keys():
        if user == user_type:
            return True
    return False

# checks if user_details has all the keys that UserDetails[user_type] has
def user_register_details(user_type, user_details: dict) -> list:
    missing_args = []
    for user_detail in UserDetails[user_type]:

        if type(user_detail) == str:
            if user_detail not in user_details:
                missing_args.append(user_detail)

        if type(user_detail) == list:
            for nested_detail in user_detail:
                if nested_detail not in user_details:
                    missing_args.append(nested_detail)
    
    return missing_args
from src.utils import USER_DETAILS, USER_TYPE_DETAILS, CONTRACT_DETAILS

# checks if user_type is a key in USER_TYPE_DETAILS
def user_type(user_type: str):
    for user in USER_TYPE_DETAILS.keys():
        if user == user_type:
            return
    raise ValueError(f"User type {user_type} not found")

# checks if user_details has all the keys that USER_TYPE_DETAILS[user_type] has
def user_register_details(user_type, payload: dict):
    missing_args = []
    for user_detail in USER_TYPE_DETAILS[user_type]:

        if type(user_detail) == str:
            if user_detail not in payload:
                missing_args.append(user_detail)

        if type(user_detail) == list:
            for nested_detail in user_detail:
                if nested_detail not in payload:
                    missing_args.append(nested_detail)
    
    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

def user_login_details(payload: dict):
    if 'username' not in payload or 'password' not in payload:
        raise ValueError("Missing username or password")        

def appointment_details(payload: dict):
    pass

def surgery_details(payload: dict):
    pass

def prescription_details(payload: dict):
    pass


def payment_details(payload: dict):
    pass

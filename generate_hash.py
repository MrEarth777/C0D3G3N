from passlib.context import CryptContext

# Create a CryptContext object to use bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password to be hashed
password = "admin123"

# Generate a hashed password
hashed_password = pwd_context.hash(password)

print("Hashed Password:", hashed_password)

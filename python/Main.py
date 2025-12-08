```python

from get_weather_new import refresh_weather
#from historic_sensor import get_last_10_days_sensors 
#from historic_weather import get_last_10_days_weather 

def main_menu():
    while True:
        print("\n🌱 Welcome to your personalized Garden System 🌱")
        print("1. Refresh Weather Forecast")
        print("2. Watering Options")
        print("3. Historic Options")
        print("4. Close")

        action = input("Select an option: ")

        if action == "1":
            refresh_weather()

        elif action == "2":
            watering_menu()

        elif action == "3":
            historic_menu()

        elif action == "4":
            print("Goodbye!")
            break  # exits main loop → program ends

        else:
            print("Invalid option. Try again.")


def watering_menu():
    while True:
        print("\n🚿 Watering Menu")
        print("1. Check Watering System")
        print("2. Manual Watering")
        print("3. Water Now")
        print("4. Back")

        option = input("Select an option: ")

        if option == "1":
            print("Checking watering system... (placeholder)")

        elif option == "2":
            print("Manual watering options... (placeholder)")

        elif option == "3":
            print("Watering now... (placeholder)")

        elif option == "4":
            break  # return to main_menu()

        else:
            print("Invalid option. Try again.")


def historic_menu():
    while True:
        print("\n Historic Menu")
        print("1. Weather Historic")
        print("2. Sensors History")
        print("3. Watering Historic")
        print("4. Back")

        option = input("Select an option: ")

        if option == "1":
            print("Showing weather history... (placeholder)")
            #get_last_10_days_weather()
        elif option == "2":
            print("Showing sensors history... (placeholder)")
            #get_last_10_days_sensors()
        elif option == "3":
            print("Showing watering history...")
        elif option == "4":
            break  # return to main_menu()

        else:
            print("Invalid option. Try again.")


# Run the app
main_menu()

```

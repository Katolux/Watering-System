"""
Legacy / exploratory entry point.
Kept as reference for planned features and system intentions.
Not used in production runtime.
"""



from get_weather_new import refresh_weather
from historic_weather import print_last_days_weather 
from repositories import add_bed_menu, list_beds_with_sensors
from db_schema import init_beds_and_sensors_tables, init_sensor_readings_table
from get_weather_new import init_weather_db


def main_menu():
    while True:
        print("\n🌱 Welcome to your personalized Garden System 🌱")
        print("-"*70)
        print("1. Refresh Weather Forecast")
        print("2. Watering Options")
        print("3. Historic Options")
        print("4. Automation and Plant Status:")
        print("5. Close")

        action = input("Select an option: ")

        if action == "1":
            refresh_weather()

        elif action == "2":
            watering_menu()

        elif action == "3":
            historic_menu()
        
        elif action == "4":
            automation_menu()
    
        elif action == "5":
            print("Goodbye!")
            break  # exits main loop → program ends

        else:
            print("Invalid option. Try again.")


def watering_menu():
    while True:
        print("\n🚿 Watering Menu")
        print("-"*70)
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
            print("Water now... (placeholder)")

        elif option == "4":
            break  # return to main_menu()

        else:
            print("Invalid option. Try again.")


def historic_menu():
    while True:
        print("\n 📜Historic Menu")
        print("-"*70)
        print("1. Weather Historic")
        print("2. Sensors History")
        print("3. Watering Historic")
        print("4. Back")

        option = input("Select an option: ")

        if option == "1":
            print("Showing weather history...")
            print_last_days_weather()
        elif option == "2":
            print("Showing sensors history... (placeholder)")
            #get_last_10_days_sensors()
        elif option == "3":
            print("Showing watering history...(placeholder)")
        elif option == "4":
            break  # return to main_menu()

        else:
            print("Invalid option. Try again.")

def automation_menu():
    while True:
        print("\n🤖 Automation Status")
        print("-"*70)
        print("1.Show Beds and Plants")
        print("2.Plants Configuration:")
        print("3. Show sensor values")
        print("4. Back")
        option = input("Choose an option:")

        if option == "1":
            print ("Showing Bed and Plants...(placeholder)")
            bed_submenu()
        elif option == "2":
            plant_submenu()
        elif option == "3":
            print("Showing Sensor Values...(placeholder)")
        elif option =="4":
            break # return main_menu()
        else:
            print("Invalid option. Try again")

def plant_submenu():
        while True:
            print("\nPlant Configuration Menu")
            print("-"*70)
            print("1.Add plant to database")
            print("2.Add Plant to bed (Plant needs to be already registered!)")
            print("3.Edit a Plant")
            print("4.Close")
            option = input("Choose an option:")

            if option == "1":
                print("Plant Database(placeholder)")
            elif option == "2":
                print("Select bed number and plant to add")
            elif option == "3":
                print ("Select plant to edit:(placeholder)")
            elif option == "4":
                break
            else :
                print("Invalid option. Try again")
              
def bed_submenu():
    while True:
        print("\nBed Management Menu")
        print("-"*70)
        print("1. Add bed")
        print("2. List beds")
        print("3. Close")
        option = input("Choose option: ")

        if option == "1":
            add_bed_menu()
        elif option == "2":
            list_beds_with_sensors()
        elif option == "3":
            break
        else :
            print("Invalid option. Try again")


def init_system():
    init_weather_db()
    init_beds_and_sensors_tables()
    init_sensor_readings_table()

if __name__ == "__main__":
    init_system()
    main_menu()



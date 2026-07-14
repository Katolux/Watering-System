from gardenhub.services import weather
import inspect

# for when the code those weird things, so we can check what code is the get weather using.
# as we have already suffered issues with duplicity of folders due to backups

print("weather service module file:", weather.__file__)
print("\n--- refresh_weather source ---\n")
print(inspect.getsource(weather.refresh_weather))



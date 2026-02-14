import get_weather_new
import inspect

# for when the code those weird things, so we can check what code is the get weather using.
# as we have already suffered issues with duplicity of folders due to backups

print("get_weather module file:", get_weather_new.__file__)
print("\n--- refresh_weather source ---\n")
print(inspect.getsource(get_weather_new.refresh_weather))



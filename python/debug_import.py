```python
import get_weather_new
import inspect

print("get_weather module file:", get_weather_new.__file__)
print("\n--- refresh_weather source ---\n")
print(inspect.getsource(get_weather_new.refresh_weather))
```

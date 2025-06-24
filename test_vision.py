

from perception import get_environment_context

import re
while True:
    context = get_environment_context()
    print(context)
    if "nothing" in context:
        print("No objects detected, exiting.")
        break
    else:
        print("Objects detected, continuing.")

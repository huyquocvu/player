# Helper functions for reading USB and parsing descriptions with tracks

"""
Each track has an accompanying description.

Match as follows:
|_ Root
  |_ audio
    |_ track1.mp3
    |_ track2.mp3
    |_ track3.mp3
    |_ ... 
  |_ descriptions
    |_ 1.txt
    |_ 2.txt
    |_ 3.txt
    |_ ...

This isn't flexible.
Let's write json or yaml

```yaml
track1:
  filename: "track1.mp3"
  name: "John Doe"
  description: "The description here"
  order: 1
track2:
  filename: "track2.mp3"
  name: "Jane Doe"
  description: "Yet another descriptive descriptor"
  order: 2
track3:
  filename: "Some_Other_Track.mp3"
  name: "Sarah Smith"
  description: "Track name can be different"
  order: 3
```
Now we're cooking. We can add more metadata if needed
"""

import os
import sys


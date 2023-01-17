# Weird live voting system thing
## Example images from running application
<img src="example-images/main-view.png" alt="Image from Main Page" width="200"/>
<img src="example-images/student-view.png" alt="Image from Student View" width="200"/>
<img src="example-images/teacher-view.png" alt="Image from Teacher View" width="200"/>

## Quickstart

Only use `python app.py`; do not use `flask run`
(for compatability with flask-socketio)

## Current method for sockets live-updating data
```mermaid
sequenceDiagram
Server ->> Client: change detected, send tcode pls
Client ->> Server: tcode (and, implictly, callback info)
Server ->> Client: change, including type and data
```
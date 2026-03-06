## **iCalPy+ (Design & Specification)**

**iCalPy+** is a planned "enrichment" engine designed to bridge the gap between static `.ics` feeds and personalized, persistent metadata.

### **The Problem**

Standard calendar feeds (Blackboard, Outlook, Google) are read-only. As a student, I want to be able to give customization such as status to many of these events.  The Blackboard ics doesn’t even give any indication to which course an event belongs, so tagging will be a feature.  

### **Proposed Architecture**

This project will implement a **Core** that handles managing events and **Views** for display:

1. **Core (Python):** Fetches `.ics` data and merges it with a local **SQLite** database.  
2. **Dev modifiable:** A dynamic schema configuration allowing developers to add local-only fields (e.g., `is_done`, `priority_level`).  
3. **Decoupled Views:** A RESTful API serving JSON to various frontend implementations (List View, Kanban, or Chart.js dashboards).

### **Planned Tech Stack**

* **Language:** Python  
* **Storage:** SQLite3  
* **Frontend:** HTML/JS/CSS
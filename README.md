# MY COMPETENCE DASHBOARD
#### Video Demo:  <https://youtube.com/shorts/g3b27Nv6SNo>
#### Description:

#### Background:
My project is intended to solve a challenge at my workplace wherein we are required to have our technical competences assessed annually. Currently, we are utilizing a purely **paper-based** approach to document and track our technical competences so I have utilized flask framework to create an application through which we can digitally track our competences.

#### App Functionality:
This app operates by allowing registration of users with passwords and subsequently allowing registered users to login. Once logged in, the app displays a list of competences that the user has in form of a table. If the logged in user is a new employee and does not have any competencies, the table displayed will only have the table headings. An employee can add a new competence by clicking *Add New Competence* on the navigation bar and a form will appear where they can type the new competence and the date on which it was assessed. Once the *Add* button is clicked, the competence list will be displayed with the new competence added along with the *Last Done Date*, *Due Date* and *Status*. The status will be *UP-TO-DATE* but as time goes by, if the current date is 2 months or less to the due date, the status will change to *ALMOST DUE* and if the current date is equal to or beyond the due date, the status will change to *OVERDUE*. When an employee's competence has been assessed, they can update by clicking on *Update competence* in the navigation bar. After they select the competence from the dropdown and update the Assessment Date, the **COMPETENCE LIST** will be returned with that particular competence's *Due date* and *Status* updated accordingly.

##### Filtering capability
The application incorporates a dynamic filtering system, enabling users to streamline their competence lists based on the status of each competence. For example, if an employee wishes to view only competences that are overdue or almost due, they can apply the relevant filter to display only those records. This functionality simplifies the management of priorities and helps users focus on competences requiring immediate attention. By reducing clutter and providing targeted insights, this feature is particularly useful in ensuring compliance with organizational standards and avoiding penalties or inefficiencies due to lapsed competences.

#### Explanation of Folders/Files in project
The project's structure is organized into various folders and files, each serving a distinct purpose. Below is a detailed explanation of each:
##### Flask seesion
This folder is dedicated to storing session data for users logged into the application. Sessions play a critical role in ensuring a seamless user experience by maintaining information about authenticated users as they navigate between different routes in the application. This secure mechanism ensures that data integrity is preserved, and users do not have to log in repeatedly during a session.

##### style.css
The style.css file houses the design and aesthetic elements of the application. It defines the visual layout, including font styles, colors, spacing, and table formatting. By adhering to a consistent design language, this file ensures a clean and user-friendly interface, enhancing the overall usability of the application.

##### apology.html
The apology.html file is a dedicated error-handling page that is displayed whenever users encounter an issue. It provides a structured way to inform users about the problem. This proactive communication minimizes user frustration and adds a layer of professionalism to the application.

##### helpers.py
This Python file contains utility functions that support the application's core functionality. Among these are the apology function for rendering error messages and the login_required decorator, which ensures that only authenticated users can access specific routes. The helpers.py file is a critical component in enforcing application security and managing user interactions effectively.

##### index.html
The index.html file serves as the application's homepage once a user logs in. It displays a comprehensive table containing all the competences of the logged-in user. The table includes columns for competence name, last done date, due date, and status. The page also features interactive elements like the filter option and navigation buttons, making it the central hub for managing competences.

##### layout.html
The layout.html file defines the overall structure and appearance of the application. Acting as a template, it prevents code repetition by including reusable components like the navigation bar, header, and footer. This modular approach simplifies development and ensures consistency across all pages.

##### login.html
This page displays a secure login form, allowing registered users to access their accounts. It features input fields for username and password, along with basic validation to ensure the entered credentials meet the application's requirements. The login.html page also includes a link for new users to register if they do not have an account.

##### new.html
The new.html file provides a form that allows users to add new competences. The form collects the competence name and the assessment date. Upon submission, the information is processed and stored in the database, updating the user's competence list accordingly. The page is user-friendly and includes helpful placeholders to guide data entry.

##### register.html
The register.html page facilitates the creation of new user accounts. It includes fields for a username, password, and password confirmation. Robust validation ensures that passwords meet security standards, and unique usernames prevent duplication. Once registration is complete, users can log in to start managing their competences.

##### update.html
The update.html file is where users can modify the "Last Done Date" of an existing competence after an assessment. A dropdown menu lists all competences for easy selection, and users can update the assessment date. Upon submission, the due date and status for the selected competence are recalculated and updated in the database. This feature helps users keep their records accurate and up-to-date.

##### app.py
The app.py file is the backbone of the application, housing all the route functions and business logic. It manages user registration, login, addition of new competences, updates to existing ones, and filtering capabilities. Built using Flask, this file interacts with the database, processes user input, and ensures that the application functions as intended. Each route is carefully designed to handle both GET and POST requests, maintaining flexibility and responsiveness.

##### competence.db
The competence.db file is a SQLite database that stores all user data, including usernames, hashed passwords, and their competences. Each competence record includes fields for competence name, last done date, due date, and status. The database structure is optimized for quick retrieval and updates, ensuring smooth performance even as the number of records grows. Regular backups are recommended to safeguard data integrity and prevent loss in case of unforeseen issues.

**This detailed explanation of the folders and files demonstrates the application's robust design and thoughtful organization, ensuring that it is maintainable, scalable, and user-friendly.**

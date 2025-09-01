# Developer Docs for The Eye - A Data Getta Product for Auburn Baseball

Last Updated: April 21, 2024 by Braden Mosley

## Domain
**https://datagetta.app**

The domain is purchased using Squarespace.
Sign in using the Google account with the email auburndatagetta@gmail.com . The password is located at **GoogleAccount.txt** on the Data Getta server.

The domain had to be setup to "point to" **datagetta.cse.eng.auburn.edu** to allow the utilization of Auburn's authentication service.

The domain will auto-renew on February 5, 2025.

## Software Utilized
- Next.js (App Router)
- React
- Material UI
- Prisma

### Docs
- Next.js - https://nextjs.org/docs
- React - https://react.dev/reference/react
- Material UI - https://mui.com/material-ui/all-components/
- Prisma - https://www.prisma.io/docs

# Next.js
It is highly recommended to become familiar with Next.js before beginning devlopment on this project.

### Key topics to begin with:
- File structure
    - https://nextjs.org/docs/app/building-your-application/routing/defining-routes
- Layout.tsx vs Page.tsx
    - https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts
    - https://nextjs.org/docs/app/api-reference/file-conventions/layout
    - https://nextjs.org/docs/app/api-reference/file-conventions/page
- Server vs Client Components
    - https://nextjs.org/docs/app/building-your-application/rendering/server-components
    - https://nextjs.org/docs/app/building-your-application/rendering/client-components
- Dynamic Routes
    - https://nextjs.org/docs/app/building-your-application/routing/dynamic-routes

## Folder Structure
All of the user interface code is located inside the **/app** folder.

Inside the **/app** folder is the layout and page for the landing page and the **/the-eye** folder.

The **/the-eye** folder houses the majority of the UI code. Putting everything inside of this folder allows for authentication to redirect you to datagetta.app/the-eye once logged in.

Inside the **/the-eye** folder, there is a folder for player related pages, team related pages, and the UI layout components.

Inside the **/player** and **/team** folder are a series of dynamic route folders that are used to query the database and fill out each of the corresponding pages.

## Dynamic Routes
Dynamic routes are utilized in this project to query the database. When passing info like player names and team names in dynamic routes, you will need to utilize the built-in function **decodeURIComponent()**. This function is used to handle special characters (like spaces) passed in a url.

- For example:
    - If the url passed is domain.com/param1 param2
    - The url will render as domain.com/param1%20param2
    - The function will replace the %20 with a space

## Authentication
Authentication is handled using Auburn's authentication service.

# Material UI
Material UI was chosen as a way to ensure and provide standard styling across the user interface. This is essential as this project will be passed from group to group. Material UI also provides a lot of functional components that are taken advantage of in this project (date pickers, bar graphs, tables, etc...). 

### WHEN DEVELOPING ON THIS PROJECT, PLEASE MAKE USE OF ALL OF MATERIAL UI'S COMPONENTS TO ENSURE CONSISTENT STYLING ACROSS THE UI.

For example, use Material UI's Typography component instead of using 'h1' - 'h6' and 'p' HTML elements.

## Links
When needing to add a link to a page, a custom Link component is located in **'/app/utils/Link.tsx'**. This component combines Next's Link component and Material UI's Link component. With Next's Link component being the primary way to navigate between routes, combining it with the Material UI's Link component adds styling to the link.

# Prisma
Prisma is used to interact with the database. Prisma provides its own query syntax, allowing you to not have to be familiar with SQL and it will provide effecient queries out-of-the-box. Unfortunately, Prisma queries do not support database features like views and functions, so you will have to make use of **'prisma.$queryRaw'** in these instances. (There are examples of both Prisma queries and raw SQL queries in this project.)

## Prisma Schema
To be able to develop locally using Prisma, you will need a **'schema.prisma'** file located in the **/prisma** folder. The **'schema.prisma'** file is created at build time on the Next app from the schema written in SQL. If the schema is ever updated, the **'schema.prisma'** file in the repository will become outdated and the newly created **'schema.prisma'** file will have to be pushed from the server after the Next app is built. After pulling the newly updated prisma schema, you will have to locally run the command **npx prisma generate** to update your local Prisma client.

### DO NOT MAKE CHANGES TO THE SCHEMA FROM THE SCHEMA.PRISMA FILE. YOU WILL HAVE TO MAKE CHANGES TO THE SCHEMA IN THE SCHEMA.SQL FILE IN THE DATABASE DIRECTORY.

## Querying the Database
One issue that was encountered when querying the database was the Postgres BigInt type. Certain Material UI components did not like the BigInt type being passed into it so the BigInt type had to be converted to the Number type. This is done by using **JSON.parse(JSON.stringify(*data*, *replacer*))** where **'data'** is the object queried from the database and **'replacer'** is the function that converts the BigInt type to the Number type. The replacer functions are located in **/app/utils/replacer.ts** .

# Future Work
- Search Bar
- Ability to hide Defensive Shift and Heat Map model tabs for non-pitchers
# onBoarder
`onBoarder` is a Data Dictionary Chatbot designed to assist new interns and staff by clarifying terms and acronyms they encounter in their new work environment. This bot operates independently of external AI services like OpenAI for basic term clarifications, ensuring real-time responsiveness and reliability. However, for in-depth explanations, `onBoarder` integrates OpenAI's capabilities to provide comprehensive insights into each term or acronym.

## Key Features
### Current Features
- **Acronym Deciphering**: Quickly deciphers acronyms to users, helping them understand company-specific terminology without delay.
- **Real-time Updating**: Ensures that all information provided is up-to-date by reflecting real-time changes made to the source tables.
- **Term Submission**: Allows users to submit tickets for new terms that are not currently in the database, facilitating continuous growth and relevance of the data dictionary.
- **Admin Authorization**: Enables admins to review and authorize submitted tickets, maintaining the accuracy and reliability of the information.
- **Term Explanation**: Provides detailed explanations of terms using OpenAI's capabilities to enhance understanding.

### Planned Features
- **Mass Database Updates**: Super admins will be able to perform bulk uploads to the database, significantly streamlining the process of updating and maintaining the data dictionary. (To be Done by End July 2024)


## Usage
Once the application is running, users can interact with `onBoarder` via telegram. The bot responds to user queries about company-specific terms and acronyms, providing quick clarifications and detailed explanations when needed.

### Examnple interactions:
- Acronym Deciphering
```
    User: /start, press 'Decipher a word'
    onBoarder: Please type the word you want the full form for:
    To cancel word search type /cancel

    User: ATOT
    onBoarder: ATOT: Actual take off time
```

- Term explanation:
```
    User: /chat
    onBoarder: Hi Onboarder here! How can I help you today?
    /cancel to exit the chatbot!
    User: what is flid?
    onBoarder: A flight identifier (FLID) is a group of alphanumeric characters used to uniquely identify a flight. This identifier is crucial for flight tracking, scheduling, and aviation safety, ensuring that each flight can be easily and accurately distinguished from another. For example, a FLID might look something like "AA1234," where "AA" often indicates the airline (in this case, American Airlines) and "1234" is a unique number assigned to a specific flight.
```

## Test it out here
@onBoarderThis1_bot
class LinkError:
    ParsingError = "Failed parse the code from the URL. Please try again!"
    AuthenticationError = "Failed to get the authentication from the URL or code provided. Please try again!"
    GeneralError = "Something went wrong when trying to link your account. Ensure you are following the instructions when linking your account. If continued errors persist, contact a adminstration."
    InvalidLink = "This is not a valid link! Run the command again and retry."
class LinkPhrases:
    Notify_User = 'I have DMed you some instructions. Please do not reply to the instructions in a public chat'
    Instructions = "Please authorize using this link: {}\n\nAfter you are authorize the application, post the resulting link in the chat which will lead you to a blank page. You have 5 minutes!\n\n# Be SURE to Dm me the link, do not post in a public channel"
    Success_1 = "Successfully completed Oauth authentication, proceed to SISU authentication for Antikick, and other higher-level methods. You may need to execute a command that requires SISU elevation to proceed to SISU Authentication. Try /Antikick"
    Success_2 = "Successfully completed SISU Authentication. You may now utilize ALL commands."
    Success_1_Queue = "Successfully completed Oauth Authentication, moving onto SISU authentication"
# DataDeck / Engage KC

This project is a core component of our 8th grade data science curriculum, designed to provide students with an interactive platform to enhance their understanding of data analysis and visualization. It allows students to create and share their data visualizations, post screenshots, and provide constructive feedback to their peers—all within a virtual learning environment. By fostering a culture of collaboration and peer review, the project helps students develop essential skills in data literacy, critical thinking, and effective communication.

The current iteration of this project is called **DataDeck**, which is accessible at [www.datadeck.dev](http://www.datadeck.dev). DataDeck is an evolving platform that, in its future state, aims to become a comprehensive Flipgrid alternative, incorporating a range of features including voice, images, text, and video to facilitate richer interactions and discussions.

## Table of Contents

1. [About the Project](#about-the-project)
2. [Getting Started](#getting-started)
3. [Contributing](#contributing)
4. [Best Practices](#best-practices)
5. [License](#license)
6. [Contact](#contact)

## About the Project

This project is being developed and maintained by PREP-KC high school students, under the guidance of their in-house developer. It's part of an educational initiative aimed at providing real-world experience to students in software development and open-source collaboration. The primary goal is to create an accessible and effective platform that replaces the functionality of Flipgrid, while tailoring it specifically to the needs of our educational environment. By focusing on features like data visualization sharing, peer feedback, and various multimedia capabilities, we are building a tool that is both versatile and impactful for students and educators alike.

This project was developed in response to the discontinuation of Flipgrid, which had been a valuable tool for our 500+ students taking the 8th grade data science course. With Flipgrid going away, we saw the need to create an educational alternative—one built by educators and students, for educators and students. DataDeck is designed to meet the specific needs of our learning community, providing a familiar yet improved experience that supports meaningful engagement and communication.

### Key Features

- **Create a Class**: Educators can easily create classes to manage student participation.
- **Generate Student Accounts**: Generate student accounts based on fun, engaging characters, making it easier for students to get started.
- **Post Data Visualizations**: Students can post their data visualizations, including screenshots, for feedback from peers.
- **Peer Feedback and Voting**: Students can leave comments and vote based on different criteria, fostering a collaborative learning environment.
- **Interactive Layouts**: The platform features fun and interactive layouts, providing a fresh way for students to engage with data online.

## Getting Started

This project is a Django-based project built on Python 3.

### Prerequisites

Make sure Python 3 is installed and run the following commands to install Django and other required packages:

```bash
pip install -r requirements.txt
```

### First Time Run

To set up the database for the first time, run:

```bash
$env:USE_MYSQL="FALSE"; python manage.py migrate
```

### Setup Admin

To create a superuser for accessing the Django admin interface, run:

```bash
$env:USE_MYSQL="FALSE"; python manage.py createsuperuser
```

### Running the Server

To start the development server, run:

```bash
$env:USE_MYSQL="FALSE"; python manage.py runserver
```
To use MySQL (connecting to your PythonAnywhere database):
```
USE_MYSQL=true python manage.py runserver
```

### Deploy Command

To collect static files for deployment, run:

```bash
python manage.py collectstatic
```

### Testing Commands

Creates a session with tons of example vizzes

```bash
python manage.py loaddata initial_data.json
```

### Maintenance Commands

#### Rebuild Vote/Comment Counts

If vote or comment counts appear incorrect (e.g., deleted comments still being counted), you can rebuild all counts from the actual data. This command operates on **all** data globally and is safe to run multiple times.

**When to use:**
- After fixing data inconsistencies
- If teachers report incorrect vote/comment totals
- As part of regular maintenance

**Usage:**

```bash
# Preview what would be updated (dry run)
python manage.py rebuild_interactions --dry-run

# Actually update the counts
python manage.py rebuild_interactions

# Also rebuild interaction comment_count fields (optional)
python manage.py rebuild_interactions --update-comment-counts
```

**What it does:**
- Recomputes `graph_likes`, `eye_likes`, and `read_likes` on all `Media` objects from actual `StudentMediaInteraction` records
- Optionally updates `StudentMediaInteraction.comment_count` fields to match actual `Comment` rows (when using `--update-comment-counts`)

**Note:** This is a CLI-only command. There is no UI button to trigger it. Only system administrators should run this command.

**Historical Context:**
Previously, when students commented on media, a `StudentMediaInteraction` record was created. These records were being counted as "votes" in the teacher dashboard, even when the student never actually voted (liked) the media. Additionally, when comments were deleted, the interaction records remained, causing phantom vote counts. This has been fixed in the code, but existing data may need to be rebuilt using this command.

### Old Commands (Not Currently Needed)

Celery Worker - No need to run currently:

```bash
celery -A datadeck worker --loglevel=info
celery -A datadeck beat --loglevel=info
```

## Contributing

We welcome contributions from anyone interested in supporting this project! Whether it's improving the documentation, fixing bugs, adding new features, or helping with other tasks, your efforts are greatly appreciated.

### How to Contribute

If you're new to open source contributions, don't worry. This project is a learning environment, especially for students who are gaining hands-on experience. We aim to make the contribution process simple and supportive.

## Best Practices

To keep things simple, we recommend that students pull directly from the main branch. This helps ensure everyone is working with the latest version of the project. However, for external contributors or more complex contributions, follow these steps:

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

### Code of Conduct

Please note that we have a [Code of Conduct](CODE_OF_CONDUCT.md) in place. All contributors are expected to adhere to it.

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](LICENSE). Feel free to use and modify the project, but make sure to include the original attribution and abide by the non-commercial terms.

## Contact

For questions or suggestions, please reach out to us:
- **Project Team Lead**: PREP-KC In-House Developer
- **Student Contributors**: PREP-KC High School Students

For more information, visit [PREP-KC's website](https://prepkc.org).

---
We appreciate your interest and look forward to building a great project together!

Together, we're not just creating a platform; we're fostering a community of young data scientists and developers. By contributing to DataDeck, you're helping to shape the future of education technology and empowering students to become data-literate citizens. Whether you're a student, educator, or professional developer, your insights and efforts can make a real difference. Let's collaborate, innovate, and inspire the next generation of data enthusiasts. Join us in this exciting journey of learning, creation, and positive impact!

## Suggested Issues and Future Features (Backlog)

We welcome contributions from external contributors. Here's a list of suggested issues and future features we're considering. These items represent our current backlog and areas where we'd appreciate community input and assistance:

- [ ] **Global Visualization Gallery**: Implement an 'ALL' page that displays visualizations from all classes, focusing on the visuals without comments or voting functionality.
- [ ] **Multi-Section Support**: Allow students to optionally select a specific section when uploading visualizations, accommodating multiple sections within a single session (e.g., "Colebank Fall '24").
- [ ] **Enhanced Media Capabilities**: Reintroduce features for recording and screen capture to enrich student submissions.
- [ ] **Improved Video Conferencing**: Transition our media solution to a more robust platform like [OpenVidu](https://openvidu.io/) or [Jitsi](https://meet.jit.si/) for better performance and features.
- [ ] **Expanded Session Visibility**: Enable teachers to make sessions public or accessible across schools/districts.
- [ ] **Shareable Session Links**: Implement functionality for creating and sharing direct links to specific sessions.
- [ ] **Official Voting System**: Develop a feature allowing teachers to initiate "official voting" where each student can vote for a limited number of entries (e.g., one to five).
- [ ] **Post Approval Workflow**: Add an option for teachers to review and approve posts before they become visible to the class.
- [ ] **Customizable Branding**: Create a system for schools or districts to apply their own branding to the platform.
- [ ] **Audio Enhancements**: Allow students to add voice-overs or short audio clips to their submissions.
- [ ] **Community Moderation**: Implement a feature for students to suggest post deletions, with a moderation queue for review.

These features are part of our vision to make DataDeck a comprehensive and engaging platform for data science education. We encourage contributors to tackle these issues or propose new ideas that align with our project goals.

# The Story behind BinksPals

Hey! Victor Pottier speaking. I am the author of BinksPals. I have deep love for computer science and the international. As a matter of fact, my dream is to travel around the world and discover everything it has to offer me. So, around September 2022, I decided to combine these two passions in a single project that I named: BinksPals. In this page, I will talk about my app story, how it evolved, from idea to conception to deployment. Without further due, let's get straight to it.

# Inspiration

My inspiration mainly came from my various penpalling experiences and observations at my high school. 

## Penpalling through short messages

My penpalling experience began in 2021, I was very excited at the idea of getting a Polish penpal from my Spanish teacher. We corresponded through social media exchanging short messages, voice messages and photos. But eventually, I realised that it was hard for me to maintain solid friendships through social media. It was always enjoyable the first time during holidays but then once back to school, both my penpal and me would get really busy with school work and other personal projects. So basically, some conversations lasted for months because I would send three to four short messages every 3-4 weeks between two exams and a coding project.

## Finding alternatives

I resolved to find an alternative to using huge social medias like Instagram or WhatsApp for penpalling and for that, I found a mobile app called Slowly. The concept was simple, your goal was to send virtual letters and meet new penpals everywhere around the world. I became literally addicted to this app around April and May 2022 until I went back to school. I couldn't ignore the app's flaws anymore. From my point of view, the app had two main flaws: 

- Inactivity, low response rate and people disabling their account: this tended to damage my own enthusiasm towards answering others and continuing using the app.
- The absence of a limit regarding the number of letters you may send: this led me to send many letters to many different people and end up overwhelmed. And there was the still the school problem which made me very busy.
- As a result, I felt pressure and a lot of shame for my late responses

After some time, I thought: why not penpalling the old way, through handwritten letters? It would take much more time to write and send the letter for sure, but I am more than convinced that receiving a long well-written letter after waiting for a very long time is way more rewarding than receiving a digital letter after 5 days or 2 weeks. And eventually, on the long term I think handwritten postal letters would work better than virtual ones and make penpalship more stable. With handwritten letters, you also have more liberties to express your creativity and your generosity since you can customise your letter as you wish and even include a small present.

I made my decision, I abandoned Slowly for another service called Global Penfriends. This website solved many of the Slowly's problems and it allowed you to meet penpals with whom you could exchange your postal address to then communicate through handwritten letters. I used it for around two months but then I still faced some major issues such as:

1. I couldn't be sure of my penpal's identity. I was constantly afraid of speaking with some kind of scammer. Therefore, I had to ask my penpals for a video call every time before giving my postal address.
2. Not everyone wished to communicate through postal letters. I mean, it's OK and the people I met who were like this have been very friendly to me but that's not what I initially aimed at when joining Global Penfriends.
3. Finding a penpal was subject to bias and I found hard to choose with whom I should penpal with next. That's because the website gave you access to a huge list of penpal profiles with a profile photo, a description, a list of hobbies and interests, etc... It seemed like doing shopping and I  don't like shopping to be honest. It's long, it's hard to make your choice, and it felt like you had to sell yourelf by trying to convince the other to click on your profile and send you a message.

As a result, finding a postal penpal was a pretty tough and time-consuming task. I wished to solve that problem and this is how BinksPals was officialy born. I wanted to **simplify** the postal penpal finding process, and make it 100% safe.

## The core ideas 

Before even starting the project, I wanted my app to have the following features:

- Penpal finding would be randomised
- But you may choose from which country your penpal should be
- You have to wait some time before using the penpal finding feature again in order to prevent abuses
- The app's security would be reinforced by exclusively granting its access to educational establishments

With that, I got all the main ideas to start making a simple app with the Python programming language. I began programming a prototype without worrying much about how the graphic interface looked just to verify if the project's technical aspects were not impossible to implement. And I eventually rejoiced when the prototype worked exactly the way I wanted it to. At this moment, I resolved to actually start building what has now become BinksPals.

## Evolution of the app's goals

At the start, all BinksPals was supposed to do was to simplify and secure the penpal finding process. But as I continued developing my project, I realised BinksPals could do much more.

After all, there aren't just students in educational establishments but teachers as well. And I doubt teachers would find anything useful in making penpals. At the same time, I noticed that my class had very few exchanges with foreign schools despite being an International British Section, which I considered as inacceptable. So I asked myself _"why?"_, is it that hard to organise exchanges between high schools?

I started searching for some reasons that would explain this phenomenon and this is how I realised that it seemed quite hard to find a teacher or a school to partner with for the exchange to begin with. And strangely enough, there seemed to be no popular tool simplifying this process despite the existence of the Internet.

All over sudden, the idea popped up in my head: BinksPals should solve that problem! For teachers, my app would be some kind of simple "school browser / search engine" where you could scroll among the schools registered in the app, access a personalised description for each one of them and request contacting a teacher from the selected school. My project then felt even more relevant as I learnt the other International British Section students from my high school had to find a penpal or a partner organisation in a foreign country (preferably in an English-speaking one such as UK, Ireland or Australia) as a part of their learning experience. All that was left to do was to turn my ideas into a mobile application

## Development

### Mobile app conception

I first had to choose which tools should I use to make my app. I first tried Android Studio, but it was really hard to get started and it slowed down my computer a lot. On top of that, I had to learn Java, which is not the programming language I'm used to.

So I preferred using Python, the programming language I master the most. I searched methods to make a mobile app with Python and found a library named **Kivy**. On contrary of Android Studio, I didn't find it much hard to learn and I got used to it quite quickly. Kivy allowed me to easily build the graphic user interface and I could deploy the app on the phone thanks to another tool called **buildozer**

### Storing data

There was still one important issue to cover: how and where the data should be stored? I first tried a quite simple solution, that is to say, storing the data on a Google Sheet and interacting with it thanks to the gspread python module. However, using gspread made it really difficult to deploy the application on the phone afterwards, as it required lots of dependencies. As we were studying databases and SQL at school, I chose to replace my current data storing system with a **mysql database**.

### Preventing cyber-attacks

But solving a problem often leads to another problem: I feared potential SQL injection attacks. I was also concerned about other vulnerabilities that could threaten the app's security. So I tried to properly format and filter the SQL requests, I also limited the number of attempts when inputting a password or any kind of key or code to prevent brute forcing. I added confirmation emails whenever someone tries to create an account or edit a password. And finally, I chose to encrypt the data stored on the database for extra but necessary security.

### Optimizing the speed

I stored some frequently used data in cache files or variables. 
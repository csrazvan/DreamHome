# DreamHome

# Problem statement 

Periodically we need to find a new home/rental. The sites that list properties have various search options but I always
found them to be a bit prescriptive and not that useful for finding our ideal home. 

For example, some of them will allow you to search for homes around a certain location whilst others will not. 
Some of them will allow you to search for particular keywords but that lacks enough power ( read it as complex expressions) or will not allow for negative keywords. 
There is none that will allow you to create some criterions and score them. 
The notification speed is sometimes low so you might find that by the time you see the notifications the property might already have been sold or there is a long queue to view the place. 

This is why I decided to build my own tool. With a bit more work it should fit perfectly the kind of usage pattern we need and it should also allow for multiple data sources (sites) to be used.
# Description 


This alpha release contains the following: 
1) You can configure the search parameters in the config.yaml file. It allows you to specify certain mandatory fields that become part of the search as well as specify other items that will be part of the computation of the score. 
2) Using a mixture of Selenium (headless browser) and plain old requests plus beautiful soup to extract data from the HTML we obtain all the information relevant to the discovered properties. 
3) A weighted score(based on config.json weights) is computed for every property and if they pass a certain threshold specified in the config file Slack APIs are used to send notifications to a Slack channel. 
4) TFL APIs are used to compute the time to certain destinations of importance ( in the current config I'm using 2 work places for my wife and I) and this is part of the score.
5) Slack client is used to send notifications to a slack channel so we can have instant feedback. 
6) Data is stored in a sqlite db via SQLAlchemy for later usage ( this needs to be added but for now even a simple CLI tool can be helpful to see what properties are available)

# Configuration 
All parameters are tunable. Weight is something that you'll have to fiddle with to get 
an understanding of what works for you. 
Most params are self-descriptive. 

## Scoring vs search fields
Search fields are used to form the search query. These are params that the site will accept in the GET request.  

Scoring params are applied post search to each individual listing.  
## Example
```
scoring:
  bathrooms:
    max_bathrooms: 2
    min_bathrooms: 2
    weight: 4
  has_garden:
    value: true
    weight: 6
  notify_at: 75
  work_locations:
    time_to_location_in_minutes: 50
    locations:
    - N1C 4BE
    - EC1M 4AR
    weight: 4
search_fields:
  areas:
    radius: 6
    seed_locations:
    - NW105BU
  bedrooms:
    max_bedrooms: 3
    min_bedrooms: 2
    weight: 4
  price:
    max_price: 2500
    min_price: 1500
    sweet_spot: 2200
    weight: 5
```

# TODO 
1. Use the available from field
2. Moar tests
3. Add positive/negative keywords and search description for them. Maybe use pynltk for a more advanced usage.  
   1. The idea here is that some words can improve the score: "newly furnished", "modern", "floor heating"
   2. While others will downgrade the score: "shared garden", "flat" when you're looking for a house.
4. Use nearby stations for time to work in case post code cannot be determined.
5. Use AWS services - run this on EC2 not your rPi, use RDS instead of sqlite, S3 for logs,etc
6. PIP compatible -> this would help with EC2 
7. Refactor selenium code to isolate and make it work with various sites 
8. Create a separate job to keep track of properties that are no longer available. 
9. Metrics for new postings per day, how fast a property is rented etc. This would be super useful to understand the market 


# Notifications
![image](https://user-images.githubusercontent.com/1096452/217949699-1484cd68-65f3-4b0a-8c8e-35c80d8e7b8a.png)

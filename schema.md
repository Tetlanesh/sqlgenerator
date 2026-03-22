# Database Schema

## Tables

| # | Table Name | URL | Status |
|---|------------|-----|--------|
| 1 | actor | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/actor | ✅ |
| 2 | address | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/address | ✅ |
| 3 | category | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/category | ✅ |
| 4 | city | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/city | ✅ |
| 5 | country | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/country | ✅ |
| 6 | customer | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/customer | ✅ |
| 7 | film | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/film | ✅ |
| 8 | film_actor | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/film-actor | ✅ |
| 9 | film_category | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/film-category | ✅ |
| 10 | film_text | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/film-text | ✅ |
| 11 | inventory | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/inventory | ✅ |
| 12 | language | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/language | ✅ |
| 13 | payment | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/payment | ✅ |
| 14 | rental | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/rental | ✅ |
| 15 | staff | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/staff | ✅ |
| 16 | store | https://dataedo.com/samples/html2/Sakila/#/doc/t3887/sakila/tables/store | ✅ |

---

## Table Details

### 1. actor
**Module:** Film  
**Description:** The actor table lists information for all actors. The actor table is referred to by a foreign key in the film_actor table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | actor_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each actor in the table. |
| 2 | | first_name | VARCHAR(45) | NO | | — | The actor's first name. |
| 3 | | last_name | VARCHAR(45) | NO | | — | The actor's last name. |
| 4 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** actor_id  
**Indexes:** idx_actor_last_name (last_name)  
**Referenced by:** film_actor.actor_id → actor.actor_id

---

### 2. address
**Module:** Customer Data  
**Description:** The address table contains address information for customers, staff, and stores. The address table primary key appears as a foreign key in the customer, staff, and store tables.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | address_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each address in the table. |
| 2 | | address | VARCHAR(50) | NO | | — | The first line of an address. |
| 3 | | address2 | VARCHAR(50) | YES | | — | An optional second line of an address. |
| 4 | | district | VARCHAR(20) | NO | | — | The region of an address (e.g. county, province). |
| 5 | FK | city_id | SMALLINT UNSIGNED | NO | | city.city_id | A foreign key pointing to the city table. |
| 6 | | postal_code | VARCHAR(10) | YES | | — | The postal code or ZIP code of the address. |
| 7 | | phone | VARCHAR(20) | NO | | — | The telephone number for the address. |
| 8 | | location | GEOMETRY | NO | | — | Spatial data (point) for the address location. |
| 9 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** address_id  
**Foreign Keys:** fk_address_city — address.city_id → city.city_id  
**Indexes:** idx_fk_city_id (city_id)  
**Referenced by:** customer.address_id, staff.address_id, store.address_id

---

### 3. category
**Module:** Film  
**Description:** The category table lists the categories that can be assigned to a film. The category table is joined to the film table via the film_category table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | category_id | TINYINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each category in the table. |
| 2 | | name | VARCHAR(25) | NO | | — | The name of the category. |
| 3 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** category_id  
**Referenced by:** film_category.category_id → category.category_id

---

### 4. city
**Module:** Customer Data  
**Description:** The city table contains a list of cities. The city table is referred to by a foreign key in the address table and refers to the country table using a foreign key.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | city_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each city in the table. |
| 2 | | city | VARCHAR(50) | NO | | — | The name of the city. |
| 3 | FK | country_id | SMALLINT UNSIGNED | NO | | country.country_id | A foreign key identifying the country that the city belongs to. |
| 4 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** city_id  
**Foreign Keys:** fk_city_country — city.country_id → country.country_id  
**Indexes:** idx_fk_country_id (country_id)  
**Referenced by:** address.city_id → city.city_id

---

### 5. country
**Module:** Customer Data  
**Description:** The country table contains a list of countries. The country table is referred to by a foreign key in the city table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | country_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each country in the table. |
| 2 | | country | VARCHAR(50) | NO | | — | The name of the country. |
| 3 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** country_id  
**Referenced by:** city.country_id → country.country_id

---

### 6. customer
**Module:** Customer Data  
**Description:** The customer table contains a list of all customers. The customer table is referred to in the payment and rental tables and refers to the address and store tables using foreign keys.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | customer_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each customer in the table. |
| 2 | FK | store_id | TINYINT UNSIGNED | NO | | store.store_id | A foreign key identifying the customer's "home store." |
| 3 | | first_name | VARCHAR(45) | NO | | — | The customer's first name. |
| 4 | | last_name | VARCHAR(45) | NO | | — | The customer's last name. |
| 5 | | email | VARCHAR(50) | YES | | — | The customer's email address. |
| 6 | FK | address_id | SMALLINT UNSIGNED | NO | | address.address_id | A foreign key identifying the customer's address in the address table. |
| 7 | | active | TINYINT(1) | NO | Default: 1 | — | Indicates whether the customer is an active customer (1 = active, 0 = inactive). |
| 8 | | create_date | DATETIME | NO | | — | The date the customer was added to the system. |
| 9 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** customer_id  
**Foreign Keys:**
- fk_customer_store — customer.store_id → store.store_id
- fk_customer_address — customer.address_id → address.address_id

**Indexes:** idx_fk_store_id (store_id), idx_fk_address_id (address_id), idx_last_name (last_name)  
**Referenced by:** payment.customer_id, rental.customer_id

---

### 7. film
**Module:** Film  
**Description:** The film table is a list of all films potentially in stock in the stores. Each row represents a single film. The film table refers to the language table and is referred to by the film_category, film_actor, and inventory tables.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | film_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each film in the table. |
| 2 | | title | VARCHAR(128) | NO | | — | The title of the film. |
| 3 | | description | TEXT | YES | | — | A short description or plot summary of the film. |
| 4 | | release_year | YEAR | YES | | — | The year in which the movie was released. |
| 5 | FK | language_id | TINYINT UNSIGNED | NO | | language.language_id | A foreign key pointing at the language table; identifies the language of the film. |
| 6 | FK | original_language_id | TINYINT UNSIGNED | YES | | language.language_id | A foreign key pointing at the language table; identifies the original language of the film. Used when a film has been dubbed into a new language. |
| 7 | | rental_duration | TINYINT UNSIGNED | NO | Default: 3 | — | The length of the rental period, in days. |
| 8 | | rental_rate | DECIMAL(4,2) | NO | Default: 4.99 | — | The cost to rent the film for the period specified in rental_duration. |
| 9 | | length | SMALLINT UNSIGNED | YES | | — | The duration of the film, in minutes. |
| 10 | | replacement_cost | DECIMAL(5,2) | NO | Default: 19.99 | — | The amount charged to the customer if the film is not returned or is returned in a damaged state. |
| 11 | | rating | ENUM('G','PG','PG-13','R','NC-17') | YES | Default: 'G' | — | The rating assigned to the film (G, PG, PG-13, R, NC-17). |
| 12 | | special_features | SET('Trailers','Commentaries','Deleted Scenes','Behind the Scenes') | YES | | — | Lists which common special features are included on the DVD. |
| 13 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** film_id  
**Foreign Keys:**
- fk_film_language — film.language_id → language.language_id
- fk_film_language_original — film.original_language_id → language.language_id

**Indexes:** idx_title (title), idx_fk_language_id (language_id), idx_fk_original_language_id (original_language_id)  
**Referenced by:** film_actor.film_id, film_category.film_id, inventory.film_id

---

### 8. film_actor
**Module:** Film  
**Description:** The film_actor table is used to support a many-to-many relationship between films and actors. For each actor in a given film, there will be one row in the film_actor table listing the actor and film.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK, FK | actor_id | SMALLINT UNSIGNED | NO | | actor.actor_id | A foreign key identifying the actor. |
| 2 | PK, FK | film_id | SMALLINT UNSIGNED | NO | | film.film_id | A foreign key identifying the film. |
| 3 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** (actor_id, film_id) — composite  
**Foreign Keys:**
- fk_film_actor_actor — film_actor.actor_id → actor.actor_id
- fk_film_actor_film — film_actor.film_id → film.film_id

**Indexes:** idx_fk_film_id (film_id)

---

### 9. film_category
**Module:** Film  
**Description:** The film_category table is used to support a many-to-many relationship between films and categories. For each category applied to a film, there will be one row in the film_category table listing the category and film.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK, FK | film_id | SMALLINT UNSIGNED | NO | | film.film_id | A foreign key identifying the film. |
| 2 | PK, FK | category_id | TINYINT UNSIGNED | NO | | category.category_id | A foreign key identifying the category. |
| 3 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** (film_id, category_id) — composite  
**Foreign Keys:**
- fk_film_category_film — film_category.film_id → film.film_id
- fk_film_category_category — film_category.category_id → category.category_id

---

### 10. film_text
**Module:** Film  
**Description:** The film_text table contains the film_id, title, and description columns of the film table, with the contents of the table kept in synchrony with the film table by means of triggers on film table INSERT, UPDATE, and DELETE operations. Used for full-text search.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | film_id | SMALLINT | NO | | — | A unique identifier matching film.film_id. |
| 2 | | title | VARCHAR(255) | NO | | — | The title of the film (copy of film.title). |
| 3 | | description | TEXT | YES | | — | The description of the film (copy of film.description). |

**Primary Key:** film_id  
**Indexes:** idx_title_description (title, description) — FULLTEXT

---

### 11. inventory
**Module:** Business  
**Description:** The inventory table contains one row for each copy of a given film in a given store. The inventory table refers to the film and store tables using foreign keys and is referred to by the rental table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | inventory_id | MEDIUMINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each item in inventory. |
| 2 | FK | film_id | SMALLINT UNSIGNED | NO | | film.film_id | A foreign key pointing to the film this item represents. |
| 3 | FK | store_id | TINYINT UNSIGNED | NO | | store.store_id | A foreign key pointing to the store stocking this item. |
| 4 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** inventory_id  
**Foreign Keys:**
- fk_inventory_film — inventory.film_id → film.film_id
- fk_inventory_store — inventory.store_id → store.store_id

**Indexes:** idx_fk_film_id (film_id), idx_store_id_film_id (store_id, film_id)  
**Referenced by:** rental.inventory_id → inventory.inventory_id

---

### 12. language
**Module:** Film  
**Description:** The language table is a lookup table listing the possible languages that films can have for their language and original language values. The language table is referred to by the film table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | language_id | TINYINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each language. |
| 2 | | name | CHAR(20) | NO | | — | The English name of the language. |
| 3 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** language_id  
**Referenced by:** film.language_id, film.original_language_id

---

### 13. payment
**Module:** Business  
**Description:** The payment table records each payment made by a customer. The payment table refers to the customer, rental, and staff tables.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | payment_id | SMALLINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key used to uniquely identify each payment. |
| 2 | FK | customer_id | SMALLINT UNSIGNED | NO | | customer.customer_id | The customer whose balance the payment is being applied to. |
| 3 | FK | staff_id | TINYINT UNSIGNED | NO | | staff.staff_id | The staff member who processed the payment. |
| 4 | FK | rental_id | INT | YES | | rental.rental_id | The rental that the payment is being applied to. NULL if the payment is for an outstanding balance. |
| 5 | | amount | DECIMAL(5,2) | NO | | — | The amount of the payment. |
| 6 | | payment_date | DATETIME | NO | | — | The date the payment was processed. |
| 7 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** payment_id  
**Foreign Keys:**
- fk_payment_customer — payment.customer_id → customer.customer_id
- fk_payment_staff — payment.staff_id → staff.staff_id
- fk_payment_rental — payment.rental_id → rental.rental_id

**Indexes:** idx_fk_customer_id (customer_id), idx_fk_staff_id (staff_id)

---

### 14. rental
**Module:** Business  
**Description:** The rental table contains one row for each rental of each inventory item with information about who rented what item, when it was rented, and when it was returned. The rental table refers to the inventory, customer, and staff tables and is referred to by the payment table.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | rental_id | INT | NO | Auto Increment | — | A surrogate primary key that uniquely identifies the rental. |
| 2 | | rental_date | DATETIME | NO | | — | The date and time that the item was rented. |
| 3 | FK | inventory_id | MEDIUMINT UNSIGNED | NO | | inventory.inventory_id | The item being rented. |
| 4 | FK | customer_id | SMALLINT UNSIGNED | NO | | customer.customer_id | The customer renting the item. |
| 5 | | return_date | DATETIME | YES | | — | The date and time the item was returned. |
| 6 | FK | staff_id | TINYINT UNSIGNED | NO | | staff.staff_id | The staff member who processed the rental. |
| 7 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** rental_id  
**Foreign Keys:**
- fk_rental_inventory — rental.inventory_id → inventory.inventory_id
- fk_rental_customer — rental.customer_id → customer.customer_id
- fk_rental_staff — rental.staff_id → staff.staff_id

**Unique Keys:** rental_date (rental_date, inventory_id, customer_id)  
**Indexes:** idx_fk_inventory_id (inventory_id), idx_fk_customer_id (customer_id), idx_fk_staff_id (staff_id)  
**Referenced by:** payment.rental_id → rental.rental_id

---

### 15. staff
**Module:** Business  
**Description:** The staff table lists all staff members, including information on email address and login credentials. The staff table refers to the store and address tables using foreign keys and is referred to by the rental, payment, and store tables.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | staff_id | TINYINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key that uniquely identifies the staff member. |
| 2 | | first_name | VARCHAR(45) | NO | | — | The first name of the staff member. |
| 3 | | last_name | VARCHAR(45) | NO | | — | The last name of the staff member. |
| 4 | FK | address_id | SMALLINT UNSIGNED | NO | | address.address_id | A foreign key to the staff member's address in the address table. |
| 5 | | picture | BLOB | YES | | — | A photograph of the employee. |
| 6 | | email | VARCHAR(50) | YES | | — | The staff member's email address. |
| 7 | FK | store_id | TINYINT UNSIGNED | NO | | store.store_id | The staff member's "home store." The employee can work at other stores but is generally assigned to the store listed. |
| 8 | | active | TINYINT(1) | NO | Default: 1 | — | Whether this is an active employee (1 = active). |
| 9 | | username | VARCHAR(16) | NO | | — | The username used by the staff member to access the rental system. |
| 10 | | password | VARCHAR(40) | YES | | — | The password used by the staff member to access the rental system (SHA1 hash). |
| 11 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** staff_id  
**Foreign Keys:**
- fk_staff_address — staff.address_id → address.address_id
- fk_staff_store — staff.store_id → store.store_id

**Indexes:** idx_fk_address_id (address_id), idx_fk_store_id (store_id)  
**Referenced by:** payment.staff_id, rental.staff_id, store.manager_staff_id

---

### 16. store
**Module:** Business  
**Description:** The store table lists all stores in the system. The store table refers to the staff and address tables using foreign keys and is referred to by the customer, inventory, and staff tables.

| # | Key | Column | Data Type | Nullable | Attributes | References | Description |
|---|-----|--------|-----------|----------|------------|------------|-------------|
| 1 | PK | store_id | TINYINT UNSIGNED | NO | Auto Increment | — | A surrogate primary key that uniquely identifies the store. |
| 2 | FK | manager_staff_id | TINYINT UNSIGNED | NO | | staff.staff_id | A foreign key identifying the manager of this store. |
| 3 | FK | address_id | SMALLINT UNSIGNED | NO | | address.address_id | A foreign key identifying the address of this store. |
| 4 | | last_update | TIMESTAMP | NO | Default: CURRENT_TIMESTAMP | — | The time that the row was created or most recently updated. |

**Primary Key:** store_id  
**Foreign Keys:**
- fk_store_staff — store.manager_staff_id → staff.staff_id
- fk_store_address — store.address_id → address.address_id

**Unique Keys:** idx_unique_manager (manager_staff_id)  
**Indexes:** idx_fk_address_id (address_id)  
**Referenced by:** customer.store_id, inventory.store_id, staff.store_id

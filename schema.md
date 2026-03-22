# Database Schema — Chinook

## Overview

The **Chinook** database models a digital music store. It contains 11 tables covering artists, albums, tracks, customers, employees, invoices, playlists, genres, and media types.

**Engine:** SQLite (file: `data/chinook.db`)

## Tables

| # | Table Name | Rows | Module |
|---|------------|------|--------|
| 1 | Album | 347 | Music Catalog |
| 2 | Artist | 275 | Music Catalog |
| 3 | Customer | 59 | Customer Data |
| 4 | Employee | 8 | Customer Data |
| 5 | Genre | 25 | Music Catalog |
| 6 | Invoice | 412 | Sales |
| 7 | InvoiceLine | 2,240 | Sales |
| 8 | MediaType | 5 | Music Catalog |
| 9 | Playlist | 18 | Music Catalog |
| 10 | PlaylistTrack | 8,715 | Music Catalog |
| 11 | Track | 3,503 | Music Catalog |

---

## Table Details

### 1. Album
**Module:** Music Catalog
**Description:** Each row represents one album, linked to an artist.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | AlbumId | INTEGER | NO | Unique album identifier. |
| 2 | | Title | NVARCHAR(160) | NO | Album title. |
| 3 | FK | ArtistId | INTEGER | NO | The artist who recorded this album. |

**Primary Key:** AlbumId
**Foreign Keys:** Album.ArtistId → Artist.ArtistId
**Indexes:** IFK_AlbumArtistId (ArtistId)
**Referenced by:** Track.AlbumId → Album.AlbumId

---

### 2. Artist
**Module:** Music Catalog
**Description:** Each row represents one music artist or band.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | ArtistId | INTEGER | NO | Unique artist identifier. |
| 2 | | Name | NVARCHAR(120) | YES | Artist or band name. |

**Primary Key:** ArtistId
**Referenced by:** Album.ArtistId → Artist.ArtistId

---

### 3. Customer
**Module:** Customer Data
**Description:** Each row represents a customer of the music store. Customers are assigned a support representative (an employee).

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | CustomerId | INTEGER | NO | Unique customer identifier. |
| 2 | | FirstName | NVARCHAR(40) | NO | Customer's first name. |
| 3 | | LastName | NVARCHAR(20) | NO | Customer's last name. |
| 4 | | Company | NVARCHAR(80) | YES | Customer's company name. |
| 5 | | Address | NVARCHAR(70) | YES | Street address. |
| 6 | | City | NVARCHAR(40) | YES | City. |
| 7 | | State | NVARCHAR(40) | YES | State or province. |
| 8 | | Country | NVARCHAR(40) | YES | Country. |
| 9 | | PostalCode | NVARCHAR(10) | YES | Postal / ZIP code. |
| 10 | | Phone | NVARCHAR(24) | YES | Phone number. |
| 11 | | Fax | NVARCHAR(24) | YES | Fax number. |
| 12 | | Email | NVARCHAR(60) | NO | Email address. |
| 13 | FK | SupportRepId | INTEGER | YES | Assigned support employee. |

**Primary Key:** CustomerId
**Foreign Keys:** Customer.SupportRepId → Employee.EmployeeId
**Indexes:** IFK_CustomerSupportRepId (SupportRepId)
**Referenced by:** Invoice.CustomerId → Customer.CustomerId

---

### 4. Employee
**Module:** Customer Data
**Description:** Staff members of the music store. Self-referencing FK for manager hierarchy (ReportsTo → EmployeeId).

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | EmployeeId | INTEGER | NO | Unique employee identifier. |
| 2 | | LastName | NVARCHAR(20) | NO | Last name. |
| 3 | | FirstName | NVARCHAR(20) | NO | First name. |
| 4 | | Title | NVARCHAR(30) | YES | Job title. |
| 5 | FK | ReportsTo | INTEGER | YES | Manager's EmployeeId (self-referencing). |
| 6 | | BirthDate | DATETIME | YES | Date of birth. |
| 7 | | HireDate | DATETIME | YES | Date hired. |
| 8 | | Address | NVARCHAR(70) | YES | Street address. |
| 9 | | City | NVARCHAR(40) | YES | City. |
| 10 | | State | NVARCHAR(40) | YES | State or province. |
| 11 | | Country | NVARCHAR(40) | YES | Country. |
| 12 | | PostalCode | NVARCHAR(10) | YES | Postal / ZIP code. |
| 13 | | Phone | NVARCHAR(24) | YES | Phone number. |
| 14 | | Fax | NVARCHAR(24) | YES | Fax number. |
| 15 | | Email | NVARCHAR(60) | YES | Email address. |

**Primary Key:** EmployeeId
**Foreign Keys:** Employee.ReportsTo → Employee.EmployeeId (self-referencing)
**Indexes:** IFK_EmployeeReportsTo (ReportsTo)
**Referenced by:** Customer.SupportRepId → Employee.EmployeeId

---

### 5. Genre
**Module:** Music Catalog
**Description:** Lookup table of music genres (Rock, Jazz, etc.).

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | GenreId | INTEGER | NO | Unique genre identifier. |
| 2 | | Name | NVARCHAR(120) | YES | Genre name. |

**Primary Key:** GenreId
**Referenced by:** Track.GenreId → Genre.GenreId

---

### 6. Invoice
**Module:** Sales
**Description:** Each row represents a sale to a customer. Contains billing address and total amount. Individual purchased items are in InvoiceLine.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | InvoiceId | INTEGER | NO | Unique invoice identifier. |
| 2 | FK | CustomerId | INTEGER | NO | Customer who made the purchase. |
| 3 | | InvoiceDate | DATETIME | NO | Date/time of the invoice. |
| 4 | | BillingAddress | NVARCHAR(70) | YES | Billing street address. |
| 5 | | BillingCity | NVARCHAR(40) | YES | Billing city. |
| 6 | | BillingState | NVARCHAR(40) | YES | Billing state/province. |
| 7 | | BillingCountry | NVARCHAR(40) | YES | Billing country. |
| 8 | | BillingPostalCode | NVARCHAR(10) | YES | Billing postal/ZIP code. |
| 9 | | Total | NUMERIC(10,2) | NO | Invoice total amount. |

**Primary Key:** InvoiceId
**Foreign Keys:** Invoice.CustomerId → Customer.CustomerId
**Indexes:** IFK_InvoiceCustomerId (CustomerId)
**Referenced by:** InvoiceLine.InvoiceId → Invoice.InvoiceId

---

### 7. InvoiceLine
**Module:** Sales
**Description:** Each row is one line item on an invoice — a single track purchase with unit price and quantity.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | InvoiceLineId | INTEGER | NO | Unique line item identifier. |
| 2 | FK | InvoiceId | INTEGER | NO | Parent invoice. |
| 3 | FK | TrackId | INTEGER | NO | Track that was purchased. |
| 4 | | UnitPrice | NUMERIC(10,2) | NO | Price per unit at time of purchase. |
| 5 | | Quantity | INTEGER | NO | Number of units purchased. |

**Primary Key:** InvoiceLineId
**Foreign Keys:**
- InvoiceLine.InvoiceId → Invoice.InvoiceId
- InvoiceLine.TrackId → Track.TrackId

**Indexes:** IFK_InvoiceLineInvoiceId (InvoiceId), IFK_InvoiceLineTrackId (TrackId)

---

### 8. MediaType
**Module:** Music Catalog
**Description:** Lookup table of media formats (MPEG, AAC, Protected AAC, etc.).

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | MediaTypeId | INTEGER | NO | Unique media type identifier. |
| 2 | | Name | NVARCHAR(120) | YES | Media type name. |

**Primary Key:** MediaTypeId
**Referenced by:** Track.MediaTypeId → MediaType.MediaTypeId

---

### 9. Playlist
**Module:** Music Catalog
**Description:** Named playlists. Linked to tracks via the PlaylistTrack junction table (M:N).

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | PlaylistId | INTEGER | NO | Unique playlist identifier. |
| 2 | | Name | NVARCHAR(120) | YES | Playlist name. |

**Primary Key:** PlaylistId
**Referenced by:** PlaylistTrack.PlaylistId → Playlist.PlaylistId

---

### 10. PlaylistTrack
**Module:** Music Catalog
**Description:** Junction table supporting M:N relationship between Playlist and Track. One row per track-in-playlist.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK, FK | PlaylistId | INTEGER | NO | The playlist. |
| 2 | PK, FK | TrackId | INTEGER | NO | The track in the playlist. |

**Primary Key:** (PlaylistId, TrackId) — composite
**Foreign Keys:**
- PlaylistTrack.PlaylistId → Playlist.PlaylistId
- PlaylistTrack.TrackId → Track.TrackId

**Indexes:** IFK_PlaylistTrackPlaylistId (PlaylistId), IFK_PlaylistTrackTrackId (TrackId)

---

### 11. Track
**Module:** Music Catalog
**Description:** Each row represents one music track. Links to Album, Genre, and MediaType. Core table of the database.

| # | Key | Column | Data Type | Nullable | Description |
|---|-----|--------|-----------|----------|-------------|
| 1 | PK | TrackId | INTEGER | NO | Unique track identifier. |
| 2 | | Name | NVARCHAR(200) | NO | Track title. |
| 3 | FK | AlbumId | INTEGER | YES | Album this track belongs to. |
| 4 | FK | MediaTypeId | INTEGER | NO | Media format of the track. |
| 5 | FK | GenreId | INTEGER | YES | Genre of the track. |
| 6 | | Composer | NVARCHAR(220) | YES | Track composer(s). |
| 7 | | Milliseconds | INTEGER | NO | Track duration in milliseconds. |
| 8 | | Bytes | INTEGER | YES | File size in bytes. |
| 9 | | UnitPrice | NUMERIC(10,2) | NO | Price per track. |

**Primary Key:** TrackId
**Foreign Keys:**
- Track.AlbumId → Album.AlbumId
- Track.GenreId → Genre.GenreId
- Track.MediaTypeId → MediaType.MediaTypeId

**Indexes:** IFK_TrackAlbumId (AlbumId), IFK_TrackGenreId (GenreId), IFK_TrackMediaTypeId (MediaTypeId)
**Referenced by:** InvoiceLine.TrackId → Track.TrackId, PlaylistTrack.TrackId → Track.TrackId

---

## Common Multi-Hop Join Paths

| From → To | Path |
|-----------|------|
| Customer → Track | `Customer → Invoice → InvoiceLine → Track` |
| Customer → Artist | `Customer → Invoice → InvoiceLine → Track → Album → Artist` |
| Customer → Genre | `Customer → Invoice → InvoiceLine → Track → Genre` |
| Invoice → Track | `Invoice → InvoiceLine → Track` |
| Invoice → Artist | `Invoice → InvoiceLine → Track → Album → Artist` |
| Track → Artist | `Track → Album → Artist` |
| Track → Playlist | `Track → PlaylistTrack → Playlist` |
| Employee → Customer | `Employee → Customer` (via SupportRepId) |
| Employee → Employee | `Employee → Employee` (via ReportsTo, self-join) |

## Schema Architecture (11 tables, 3 modules)

- **Music Catalog:** `Artist`, `Album`, `Track`, `Genre`, `MediaType`, `Playlist`, `PlaylistTrack` (M:N)
- **Customer Data:** `Customer`, `Employee` (self-referencing hierarchy)
- **Sales:** `Invoice`, `InvoiceLine`

Key structural patterns:
- M:N relationship between playlists and tracks uses `PlaylistTrack` junction table with **composite PK**
- `Employee.ReportsTo` is a **self-referencing FK** for the management hierarchy
- Address fields are **denormalized** directly on `Customer`, `Employee`, and `Invoice` (no separate address table)
- `InvoiceLine` connects sales to the music catalog — it's the bridge between the Sales and Music Catalog modules

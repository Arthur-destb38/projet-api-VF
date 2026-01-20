@property
    def search_url(self) -> str:
        """Construct the advanced search URL based on configuration."""
        encoded_query = urllib.parse.quote(self.config.query)
        base = f"https://x.com/search?q={encoded_query}"

        filters = []
        if self.config.min_replies:
            filters.append(f"min_replies%3A{self.config.min_replies}")
        if self.config.min_likes:
            filters.append(f"min_faves%3A{self.config.min_likes}")
        if self.config.min_reposts:
            filters.append(f"min_retweets%3A{self.config.min_reposts}")
        if self.config.start_date:
            filters.append(f"since%3A{self.config.start_date}")
        if self.config.end_date:
            filters.append(f"until%3A{self.config.end_date}")

        if filters:
            base += "%20" + "%20".join(filters)

        return f"{base}&src=typed_query&f=live"
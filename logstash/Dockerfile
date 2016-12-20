FROM logstash:5

# Add your logstash plugins setup here
# Example: 
RUN logstash-plugin install logstash-filter-grok logstash-filter-date logstash-input-syslog

COPY config/logstash.conf /etc/logstash/conf.d/

CMD ["-f", "/etc/logstash/logstash.conf"]
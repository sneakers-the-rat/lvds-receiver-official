# Site filters: thousands separators for the token totals, and
# Pacific-time rendering of the site's UTC timestamps (user
# directive 2026-11-04: plot/display timestamps in Pacific time,
# not UTC). The data stays UTC; only the display converts.
require "time"

module PdlvdsFilters
  # 133920588 -> "133,920,588"
  def number_delimiter(input, delimiter = ",")
    return "" if input.nil?

    input.to_s.gsub(/(\d)(?=(\d{3})+(?!\d))/, "\\1#{delimiter}")
  end

  # "2026-11-04T10:08:43Z" -> "2026-11-03 02:08 PST" (format is a
  # strftime string; %Z gives PST/PDT as appropriate for the date).
  def pacific(input, format = "%Y-%m-%d %H:%M %Z")
    return "" if input.nil? || input.to_s.empty?

    t = input.is_a?(Time) ? input : Time.parse(input.to_s)
    old_tz = ENV["TZ"]
    begin
      ENV["TZ"] = "America/Los_Angeles"
      t.getlocal.strftime(format)
    rescue StandardError
      input.to_s
    ensure
      ENV["TZ"] = old_tz
    end
  end
end

Liquid::Template.register_filter(PdlvdsFilters)

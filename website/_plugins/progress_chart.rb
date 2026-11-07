# Pass-history progress chart generator.
#
# Reads the passes collection's front matter (the same stats
# scripts/commit_pass.py records for every pass: unconnected_nets
# and clearance_violations, from each pass's board audit) and emits
# assets/gen/progress.svg at build time — two stacked panels sharing
# the pass axis: unconnected nets and clearance violations, each
# with 0 at the bottom, so the project's story (both series falling
# to 0) reads at a glance. No hand-maintained data, no JS library.
#
# Why n disconnected and not % connected: the only nets_total in
# the pass metadata is 112, recorded for the first five passes of
# the ORIGINAL board; the corrected schematic's netlist has 223
# nets (results/partsfix/netlist-final.txt), so no single
# denominator spans the series and a percentage would be fiction.
require "time"

module PdlvdsProgress
  class ProgressChartGenerator < Jekyll::Generator
    safe true
    priority :low

    W = 960
    MARGIN_L = 58
    MARGIN_R = 64
    PANEL_H = 196
    PANEL_GAP = 64
    TOP = 64

    def generate(site)
      docs = (site.collections["passes"]&.docs || [])
      rows = docs.map do |d|
        {
          pass: d.data["pass"],
          timestamp: d.data["timestamp"],
          unconnected: d.data["unconnected_nets"],
          violations: d.data["clearance_violations"]
        }
      end.select { |r| r[:pass] }.sort_by { |r| r[:pass] }

      page = Jekyll::PageWithoutAFile.new(site, site.source, "assets/gen", "progress.svg")
      page.content = build_svg(rows)
      page.data["layout"] = nil
      page.data["sitemap"] = false
      site.pages << page
    end

    private

    def pacific(ts, fmt)
      return "" if ts.nil? || ts.to_s.empty?

      t = ts.is_a?(Time) ? ts : Time.parse(ts.to_s)
      old = ENV["TZ"]
      begin
        ENV["TZ"] = "America/Los_Angeles"
        t.getlocal.strftime(fmt)
      rescue StandardError
        ts.to_s
      ensure
        ENV["TZ"] = old
      end
    end

    def esc(s)
      s.to_s.gsub("&", "&amp;").gsub("<", "&lt;").gsub(">", "&gt;")
    end

    def panel(rows, key, title, color, y_off, x0, x1, plot_w)
      pts = rows.select { |r| !r[key].nil? }
      return "" if pts.empty?

      max_v = pts.map { |r| r[key] }.max
      max_v = 1 if max_v.nil? || max_v <= 0
      y_max = (max_v * 1.08).ceil
      sx = ->(p) { x0 + (p - x0_pass(rows)) * plot_w / pass_span(rows).to_f }
      sy = ->(v) { y_off + PANEL_H - (v * PANEL_H / y_max.to_f) }

      out = +""
      out << %(<text x="#{MARGIN_L}" y="#{y_off - 14}" fill="#d7e5f2" font-size="15" font-weight="700">#{esc(title)}</text>)
      # horizontal gridlines at 0, 1/3, 2/3, max
      [0.0, 1.0 / 3, 2.0 / 3, 1.0].each do |f|
        v = y_max * f
        y = sy.call(v)
        out << %(<line x1="#{MARGIN_L}" y1="#{'%.1f' % y}" x2="#{MARGIN_L + plot_w}" y2="#{'%.1f' % y}" stroke="#2c3e50" stroke-width="1"/>)
        out << %(<text x="#{MARGIN_L - 8}" y="#{'%.1f' % (y + 4)}" fill="#9db8d2" font-size="11" text-anchor="end">#{v.round}</text>)
      end
      line = pts.map { |r| "#{'%.1f' % sx.call(r[:pass])},#{'%.1f' % sy.call(r[key])}" }.join(" ")
      out << %(<polyline points="#{line}" fill="none" stroke="#{color}" stroke-width="2"/>)
      pts.each do |r|
        out << %(<circle cx="#{'%.1f' % sx.call(r[:pass])}" cy="#{'%.1f' % sy.call(r[key])}" r="2" fill="#{color}"/>)
      end
      last = pts.last
      out << %(<text x="#{'%.1f' % (sx.call(last[:pass]) + 8)}" y="#{'%.1f' % (sy.call(last[key]) + 4)}" fill="#{color}" font-size="13" font-weight="700">#{last[key]} (pass #{last[:pass]})</text>)
      out
    end

    def x0_pass(rows)
      rows.map { |r| r[:pass] }.min || 1
    end

    def pass_span(rows)
      span = (rows.map { |r| r[:pass] }.max || 1) - x0_pass(rows)
      span <= 0 ? 1 : span
    end

    def build_svg(rows)
      plot_w = W - MARGIN_L - MARGIN_R
      total_h = TOP + PANEL_H * 2 + PANEL_GAP + 64
      x0 = x0_pass(rows)
      span = pass_span(rows)
      sx = ->(p) { MARGIN_L + (p - x0) * plot_w / span.to_f }

      out = +%(<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 #{W} #{total_h}" width="100%" role="img" aria-label="Layout progress: unconnected nets and clearance violations per pass">)
      out << %(<rect x="0" y="0" width="#{W}" height="#{total_h}" fill="#111111"/>)
      out << %(<text x="#{MARGIN_L}" y="30" fill="#ffffff" font-size="17" font-weight="700">Board progress by pass</text>)
      if rows.any?
        last_ts = rows.map { |r| r[:timestamp] }.compact.last
        out << %(<text x="#{MARGIN_L}" y="50" fill="#9db8d2" font-size="12">Generated at build time from the passes metadata (scripts/commit_pass.py audit stats). Latest: pass #{rows.last[:pass]}#{last_ts ? ", #{esc(pacific(last_ts, '%Y-%m-%d %H:%M %Z'))}" : ''}.</text>)
      end
      out << panel(rows, :unconnected, "Unconnected nets — target 0", "#34c759", TOP, x0, span, plot_w)
      out << panel(rows, :violations, "Clearance violations — target 0", "#ff9f0a", TOP + PANEL_H + PANEL_GAP, x0, span, plot_w)

      # x axis: pass ticks + Pacific date labels under the bottom panel
      axis_y = TOP + PANEL_H * 2 + PANEL_GAP
      ticks = [1, 25, 50, 75, 100].select { |t| t <= (x0 + span) } + [x0 + span]
      ticks.uniq.each do |t|
        x = sx.call(t)
        out << %(<line x1="#{'%.1f' % x}" y1="#{axis_y}" x2="#{'%.1f' % x}" y2="#{axis_y + 5}" stroke="#9db8d2" stroke-width="1"/>)
        out << %(<text x="#{'%.1f' % x}" y="#{axis_y + 20}" fill="#9db8d2" font-size="11" text-anchor="middle">pass #{t}</text>)
      end
      dated = rows.select { |r| r[:timestamp] }
      if dated.any?
        [dated.first, dated[dated.length / 2], dated.last].uniq.each do |r|
          x = sx.call(r[:pass])
          out << %(<text x="#{'%.1f' % x}" y="#{axis_y + 38}" fill="#7e97ad" font-size="11" text-anchor="middle">#{esc(pacific(r[:timestamp], '%b %-d'))}</text>)
        end
      end
      out << "</svg>"
      out
    end
  end
end

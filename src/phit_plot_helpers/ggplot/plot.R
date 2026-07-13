barplot <- function(plot_data,plot_title,plot_subtitle,plot_caption,point_shift){
  
  # set position for shape
  # nb1: given $ sets a value within a vactor/map, this is probably setting a constant value
  plot_data$point.position <- point_shift
  
  # # Clean up filter name column
  # plot_data$clean.name <- plot_data$filter.name
  # plot_data$clean.name <- gsub("_"," ",plot_data$clean.name)
  # plot_data$clean.name <- str_to_title(plot_data$clean.name)
  # plot_data$clean.name <- gsub("And","&",plot_data$clean.name)
  # 
  # # set the order and then factor
  # sort_filters <- plot_data$clean.name[plot_data$clean.name != "England"][order(-plot_data$value[plot_data$clean.name != "England"])]
  # sort_filters <- c(sort_filters,"England")
  # plot_data$clean.name <- factor(plot_data$clean.name, levels = sort_filters)
  
  # nb2: this function depends on external variables defined outside of the function parameters. 
  # plod_data$clean.name must have been created
  gg <- ggplot(plot_data, aes(x = clean.name, y = value)) +
    geom_col(aes(fill = compared.to.england), show.legend = FALSE) +
    # nb1: so given the only place this constant is used is here, could the point_shift value be used directly?
    geom_point(aes(clean.name, point.position, shape = compared.to.england, fill = compared.to.england), size = 2.5, show.legend = T) +
    geom_errorbar(aes(ymin=LCI, ymax=UCI), width = 0.3, colour = "black") +
    xlab(NULL) + ylab("\nAge standardised rate (per 100,000)") +
    scale_y_continuous(expand = expansion(mult = c(0.04, 0.05))) +
    labs(title = plot_title,
         subtitle = plot_subtitle,
         caption = plot_caption) +
    #coord_flip() +
    scale_shape_manual(
      name = "Compared to England",
      values = c("worse" = 24,"similar" = 22,"better" = 23,"not.compared" = 21),
      labels = c(worse = "Worse",similar = "Similar",better = "Better",not.compared = "Not Compared"),
      drop = FALSE
    ) +
    scale_fill_manual(
      name = "Compared to England",
      values = c("worse" = "#B50401","similar" = "#F7BF00","better" = "#99CF48","not.compared" = "darkgrey"),
      labels = c(worse = "Worse",similar = "Similar",better = "Better",not.compared = "Not Compared"),
      drop = FALSE
    ) +
    theme_minimal()
  
  return(gg)
  
}

barplot <- function(plot_data,plot_title,plot_subtitle,plot_caption,point_shift){
    # create a ggplot visualisation for plot_data,
    # a geom_col barplot with  
    # plot_data is a dataframe containing the following:
    # - clean.name
    # - value
    # - compared.to.england
    # - LCI
    # - UCI
    # point_shift is set in order to move the plot into the correct position, it is generally set to -40 or -70

    gg <- ggplot(plot_data, aes(x = clean.name, y = value)) +
        geom_col(
            aes(fill = compared.to.england), 
            show.legend = FALSE
        ) +
        geom_point(
            aes(clean.name, point_shift, shape = compared.to.england, fill = compared.to.england), 
            size = 2.5, 
            show.legend = T
        ) +
        geom_errorbar(
            aes(ymin=LCI, ymax=UCI), 
            width = 0.3, 
            colour = "black"
        ) +
        scale_y_continuous(expand = expansion(mult = c(0.04, 0.05))) +
        labs(
            x = NULL,
            y = "\nAge standardised rate (per 100,000)",
            title = plot_title,
            subtitle = plot_subtitle,
            caption = plot_caption
        ) +
        #coord_flip() +
        scale_shape_manual(
            name = "Compared to England",
            values = c("worse" = 24,"similar" = 22,"better" = 23,"not.compared" = 21),
            labels = c(worse = "Worse",similar = "Similar",better = "Better",not.compared = "Not Compared"),
            drop = FALSE
        ) +
        scale_fill_manual(
            name = "Compared to England",
            values = c("worse" = "#B50401","similar" = "#F7BF00","better" = "#99CF48","not.compared" = "darkgrey"),
            labels = c(worse = "Worse",similar = "Similar",better = "Better",not.compared = "Not Compared"),
            drop = FALSE
        ) +
        theme_minimal()
    
    return(gg)
  
}